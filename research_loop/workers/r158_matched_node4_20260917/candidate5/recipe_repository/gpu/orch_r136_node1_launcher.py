"""A100-only R136 staging and saved-generation-boundary retirement.

No process is stopped merely because nvidia-smi has a gap. The inference-only
retirement path checks a fresh saved cursor while the exact actor and its
supervisor are paused, archives and verifies evidence, then disables those
two identities. A separate saved-carry path handles read-only math residents;
neither retirement path handles active training consumers.
"""

import argparse
import ctypes
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import shutil
import socket
import stat
import struct
import subprocess
import sys
import tarfile
import time
from types import SimpleNamespace
import uuid

from gpu import orch_r125_continual_native as native
from gpu import orch_r133_retire_old_lanes as preservation
from organism_v6.orch_r125_plain_context import VERSION


BASE = Path('/localhome/local-rohing')
GENERATION_ROOT = BASE/'orch_r119_l1_generation_20260915_attempt2'
MATH_ROOT = BASE/'orch_math_feedback_uptake_r122_a100_20260915_attempt2'
MATH_SOURCE = BASE/'orch_math_feedback_uptake_r122_oldfleet_source_20260915_v2'
MATH_MODULE = 'gpu.orch_math_feedback_uptake_r122_a100'
CONSUMER_ROOT = BASE/'orch_r132_gen7_consumer_20260915_attempt1'
PYTHON = BASE/'v2/venv/bin/python'
DEVICES = {
    0: 'GPU-ff5f84e9-c70e-272d-a8e0-eb20aad05ac6',
    1: 'GPU-604c4ea8-8c29-099e-76ed-571ec7d9be4b',
    2: 'GPU-8e15ce78-4e9c-4c48-724f-2b753c6c2296',
    3: 'GPU-631f3e6a-fbce-0ec5-b934-f08dd64634f8',
    4: 'GPU-31583768-d90f-520c-51ed-5dac761526d0',
    5: 'GPU-c1650c7f-ac26-f1a0-2ab8-c7354a6f27c9',
    6: 'GPU-6de3930d-104a-f969-7d36-009271368dd1',
    7: 'GPU-f0405a96-813d-7ac7-d641-3ec31d103037',
}
LANES = {
    0: ('frozen_adapter', 'raw_parented', 3, 'supportive', 'no_distillation'),
    1: ('base_only', 'raw_parented', 3, 'Socratic', 'no_distillation'),
    2: ('teach_replay', 'raw_parented', 2, 'scaffold-fading', 'free_distillation'),
    3: ('teach_perception', 'raw_parented', 1, 'contrastive', 'reread_select'),
    4: ('teach_parenting', 'raw_parented', 3, 'reflective-coach', 'parent_guided_distillation'),
    5: ('classroom_brain', 'brain_lecture', 3, 'explanatory', 'free_distillation'),
    6: ('classroom_creative', 'creative_writing', 2, 'workshop', 'reread_select'),
    7: ('classroom_support', 'emotional_support', 4, 'validating-inquisitive', 'no_distillation'),
}
PROGRAMMES = {
    2: 'Your conversational parent will explore with you how to choose, revisit and consolidate useful experience. '
       'Try replay strategies, compare predictions with what happened, and notice when support is no longer needed. '
       'You need not adopt a recurring thought template or assume that replay guarantees learning.',
    3: 'Your conversational parent will explore perception with you: separate observations, interpretations and '
       'predictions, compare contrasting cases, and test what changes your judgment. Do not invent an observation '
       'or claim access to sensory inputs or tools that are not actually connected.',
    4: 'Your conversational parent will explore how to parent another language-model learner: listen, ask useful '
       'questions, give feedback and reflect on what the other learner actually did. Any peer material must arrive '
       'as attributed environment input from a real TRAIN child, not as private parent dialogue. Peer relay is '
       'not yet connected; do not invent another child or an exchange.',
    5: 'Your conversational parent will teach a brain and memory seminar, carefully distinguishing retrieved '
       'human-neuroscience evidence from untested analogies to your context and adapter. Classroom peer exchange '
       'is pending a separate verified relay; only actual attributed peer messages count as received.',
    6: 'Your conversational parent will lead a creative-writing workshop: draft, receive critique, revise and '
       'explore alternatives. No praise for length or required introspective format. Classroom peer exchange '
       'is pending a separate verified relay; only actual attributed peer messages count as received.',
    7: 'Your conversational parent will ask supportive questions about your actual activity, judgments and '
       'uncertainty. This is not therapy for a human or evidence that you have feelings. Classroom peer exchange '
       'is pending a separate verified relay; only actual attributed peer messages count as received.',
}


def require(condition, reason):
    native.require(condition, reason)


def ref(path):
    return preservation.ref(path)


def write(path, document):
    preservation.immutable(path, document)


def generation_provenance(root=GENERATION_ROOT):
    forks = native.read(root/'FORKS.json')
    require(forks['node'] == 'a100' and forks['uuid_by_index'] == list(DEVICES.values()), 'exact_A100_generation_binding')
    require(forks['hard_deadline_unix'] <= forks['lease_end_unix']-21600
        and time.time()+600 < forks['hard_deadline_unix'], 'inherited_A100_lease_margin')
    wrapper = root/'orch_r119_l1_generation_resume.py'
    generator = Path(forks['pythonpath'].split(':')[0])/'orch_r109_l1_generation_v3.py'
    require(native.sha(wrapper) == forks['wrapper_sha256'] == preservation.WRAPPER_SHA,
            'reviewed_generator_wrapper')
    require(native.sha(generator) == forks['generator_sha256'] == preservation.GENERATOR_SHA,
            'reviewed_generator_source')
    seed = preservation.checkpoint(forks['checkpoint'])
    require(seed['commit']['sha256'] == forks['checkpoint_commit_sha256'], 'exact_ancestral_seed')
    return forks, dict(forks=ref(root/'FORKS.json'), wrapper=ref(wrapper), generator=ref(generator), seed=seed)


def validate_pair(request):
    require(request['node'] == 'a100' and type(request['physical']) is int
        and request['physical'] in (2, 3, 4), 'generation_lanes_only_no_training_signals')
    physical, segment = request['physical'], request['segment']
    require(type(segment) is int and segment >= 0, 'explicit_segment')
    actor, supervisor = request['actor'], request['supervisor']
    prefix = [str(PYTHON), '-B', '-u', str(GENERATION_ROOT/'orch_r119_l1_generation_resume.py')]
    require(actor['argv'] == prefix+['generate', '--root', str(GENERATION_ROOT), '--index', str(physical), '--segment', str(segment)]
        and supervisor['argv'] == prefix+['supervise', '--root', str(GENERATION_ROOT), '--index', str(physical)],
        'exact_generation_actor_and_supervisor')
    require(actor['uid'] == supervisor['uid'] == os.getuid() and actor['parent'] == supervisor['pid'], 'owned_process_pair')
    require(actor['cvd'] == [DEVICES[physical]] and supervisor['cvd'] == [''], 'exact_GPU_and_CPU_bindings')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
        and '2026-09-16' in request['gate']['builder_line'], 'dated_own_CPU_gate')
    require(1 <= request['wait_seconds'] <= 300, 'bounded_retirement_wait')


def boundary_event(events, marker=b'PROGRESS.json'):
    cursor = 0
    while cursor+16 <= len(events):
        descriptor, mask, cookie, length = struct.unpack_from('iIII', events, cursor)
        require(cursor+16+length <= len(events), 'complete_inotify_event')
        name = events[cursor+16:cursor+16+length].rstrip(b'\0')
        if name == marker and mask & (0x8 | 0x80):
            return True
        cursor += 16+length
    return False


def scan(config_path, output):
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(Path(__file__).resolve().parents[1]), str(PYTHON), '-B', '-m',
        'gpu.orch_r125_continual_guard', 'scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(command, text=True, timeout=90))
    write(output, report)
    return report


def retire_generation(request, output):
    validate_pair(request)
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    forks, proof = generation_provenance()
    require(time.time()+request['wait_seconds']+600 < forks['hard_deadline_unix'], 'retirement_within_lease')
    from gpu.orch_r125_continual_guard import validate
    config, plan = validate(request['scan_config'])
    require(plan['physical'] == request['physical'] and plan['gpu_uuid'] == DEVICES[request['physical']], 'release_scan_same_slot')
    physical, actor, supervisor = request['physical'], request['actor'], request['supervisor']
    directory = GENERATION_ROOT/f'gpu{physical}'/f"segment{request['segment']:04d}"/f'gpu{physical}'
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', dict(request=request, provenance=proof, started_unix=time.time()))
    started, deadline = time.time(), time.monotonic()+request['wait_seconds']
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    require(watch >= 0, 'inotify_required')
    descriptors, paused = {}, []
    pair = [('supervisor', supervisor), ('actor', actor)]
    def interrupted(signum, frame):
        raise SystemExit('operator_interrupted_resume_exact_owned_processes')
    old_handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        require(library.inotify_add_watch(watch, os.fsencode(directory), 0x8 | 0x80) >= 0, 'watch_exact_cursor')
        for label, process in pair:
            preservation.same(process)
            descriptors[label] = os.pidfd_open(process['pid'])
            preservation.same(process)
        attempts = 0
        while time.monotonic() < deadline:
            if not select.select([watch], [], [], 1)[0]:
                for label, process in pair:
                    preservation.same(process)
                continue
            if not boundary_event(os.read(watch, 65536)):
                continue
            attempts += 1
            try:
                for label, process in pair:
                    paused.append((label, process))
                    preservation.pause(process, descriptors[label])
                require(native.read(directory/'PROGRESS.json')['finished_unix'] >= started, 'new_boundary_not_stale')
                boundary = preservation.frontier(directory)
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
                write(output/f'REJECTED_{attempts:04d}.json', dict(error=str(error), observed_unix=time.time()))
                for label, process in reversed(paused):
                    signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                paused.clear()
                continue
            write(output/'BOUNDARY.json', boundary)
            saved = preservation.archive([GENERATION_ROOT/f'gpu{physical}', GENERATION_ROOT/'FORKS.json',
                Path(forks['checkpoint']), proof['wrapper']['path'], proof['generator']['path']], output/'STATE.tar')
            require(preservation.frontier(directory) == boundary, 'frontier_still_saved_after_archive')
            write(output/'PRESERVATION.json', dict(**saved, active_optimizer='ABSENT_GENERATION_ONLY',
                live_generation_RNG='NOT_EXPORTED; NO_BITWISE_GENERATION_RESUME_CLAIM',
                own_carry='NO_OWN_CARRY_FIELD; FULL_EPISODES_AND_CURSOR_PRESERVED',
                ancestral_optimizer_and_rank_rng='VERIFIED_AND_ARCHIVED', observed_unix=time.time()))
            for label, process in reversed(pair):
                preservation.same(process)
                signal.pidfd_send_signal(descriptors[label], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                require(bool(select.select([descriptors[label]], [], [], 30)[0]), 'owned_exit_no_KILL_escalation')
            paused.clear()
            report = scan(request['scan_config'], output/'RELEASE_SCAN.json')
            require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
                and report['gpu']['uuid'] == DEVICES[physical], 'fresh_exclusive_release_required')
            receipt = dict(status='RELEASED', physical=physical, gpu_uuid=DEVICES[physical],
                actor=actor, disabled_supervisor=supervisor, preservation=ref(output/'PRESERVATION.json'),
                scan=ref(output/'RELEASE_SCAN.json'), finished_unix=time.time(), other_slots_touched=False)
            write(output/'RELEASED.json', receipt)
            return receipt
        write(output/'WAIT_EXPIRED.json', dict(status='WAIT_EXPIRED_NO_RELEASE', attempts=attempts, finished_unix=time.time()))
    except BaseException as error:
        write(output/'ERROR.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        for label, process in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(watch)
        for signum, handler in old_handlers.items():
            signal.signal(signum, handler)


def classroom_startup(template, source, physical, life_root):
    require(physical in (5, 6, 7), 'classroom_startup_only')
    text = template
    old_resource = next(line for line in text.splitlines() if line.startswith('You run on one assigned GPU,'))
    old_lease = next(line for line in text.splitlines() if line.startswith('The initial pilot has at most'))
    replacements = {
        '/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/workspace': str(Path(life_root)/'workspace'),
        '/localhome/local-rohing/orch_r127_pilot_20260916_attempt1/source1': str(source),
        old_resource: f'You run on one assigned A100 GPU, physical{physical} through the a100 wrapper. '
            'No automatic executor, network, credentials, shared-filesystem access or other GPU is connected. '
            'Ask Astra for an operator-mediated operation; only actual attributed Tool results establish execution. '
            'You may continue while replies are pending.',
        old_lease: 'The current allocation ends no later than September 26, 2026 at 17:05 UTC, '
            'preserving the existing six-hour lease margin. No additional allocation is implied.',
    }
    if physical == 6:
        replacements['distill what you want to retain in a third segment'] = (
            're-read your visible history and select passages to retain in a third segment')
    if physical == 7:
        replacements['After two generated segments, the runtime invites you to distill what you want to retain '
            'in a third segment, then sleeps.'] = ('After two generated segments, the runtime sleeps without '
            'requesting a summary or generating a third distillation segment.')
        replacements['At sleep your nonempty distillation replaces the earlier visible history with your own summary. '
            'This is lossy: the full raw archive is preserved but not all of it stays visible.'] = (
            'Sleep does not summarize or compact your visible history in this condition; it remains visible '
            'subject to the same ordinary context-limit eviction. The full raw archive is preserved.')
    for before, after in replacements.items():
        require(text.count(before) == 1, 'exact_truthful_startup_template')
        text = text.replace(before, after)
    return text.rstrip()+f'\n\n### Programme: {LANES[physical][0]}\n\n'+PROGRAMMES[physical]+'\n'


def stage(source, output, physical, startup, cpu_receipt, base_commit, contained=False):
    require(socket.gethostname() == '[REDACTED_HOST]' and physical in range(2, 8), 'A100_learning_stage_only')
    source, output, startup, cpu_receipt = map(Path, (source, output, startup, cpu_receipt))
    require(re.fullmatch(r'[0-9a-f]{40}', base_commit) is not None, 'exact_committed_base_identifier')
    require(source.resolve() == Path(__file__).resolve().parents[1] and startup.resolve().is_relative_to(source.resolve()),
            'actual_pinned_source_and_startup')
    cpu = native.read(cpu_receipt)
    require(cpu['passed'] is True and cpu['tests'] > 0 and cpu['source_pins'] == {
        str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}, 'actual_CPU_tested_closure')
    forks, proof = generation_provenance()
    output.mkdir(parents=True, exist_ok=False)
    lease = dict(lease_end_unix=forks['lease_end_unix'], hard_end_unix=forks['hard_deadline_unix'],
        inherited_from=proof['forks'], original_margin_seconds=21600, extension=False)
    write(output/'LEASE.json', lease)
    variant = LANES[physical][4]
    plan = dict(schema=native.SCHEMA, base_sha256=native.BASE_SHA256, system_prompt=native.SYSTEM,
        birth_prompt=startup.read_text(), startup_context=dict(version='R127_STARTUP_V1', path=str(startup), sha256=native.sha(startup)),
        compaction_invitation=native.PRESLEEP_INVITATIONS[variant], presleep_variant=variant, seed=0,
        new_presentations=16, rehearsal_presentations=1, anchor_lambda=0.25, segments_per_sleep=2,
        segment_tokens=512, context_limit=16384, presentation_version=VERSION, max_sleeps=None,
        physical=physical, gpu_uuid=DEVICES[physical], hard_end_unix=lease['hard_end_unix'], lease_end_unix=lease['lease_end_unix'],
        decoder=dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16),
        root=str(output.parent/'run1'), source_root=str(source), model_dir=forks['model_dir'],
        anchors=str(BASE/'orch_r107_base_anchors_20260915_attempt1'))
    require(not Path(plan['root']).exists(), 'new_life_no_reset')
    native.validate_plan(plan)
    write(output/'PLAN.json', plan)
    write(output/'ALLOCATION.json', dict(schema='R125_NATIVE_ALLOCATION_V1',
        builder_entry='Published R134 A100 allocation plus independent R136 CPU/provenance gate', builder_entry_pushed=True,
        builder_commit=base_commit, current_CPU_gate_pushed=False, source_overlay_independently_pinned=True,
        cpu_tests_passed=True, cpu_receipt_path=str(cpu_receipt), cpu_receipt_sha256=native.sha(cpu_receipt),
        declared_unix=time.time(), physical=physical, gpu_uuid=DEVICES[physical], plan_sha256=native.sha(output/'PLAN.json')))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', allocation_path=str(output/'ALLOCATION.json'),
        allocation_sha256=native.sha(output/'ALLOCATION.json'), attempt_dir=str(output), hard_end_unix=lease['hard_end_unix'],
        host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(), lease_path=str(output/'LEASE.json'),
        lease_sha256=native.sha(output/'LEASE.json'), next_reserved_unix=lease['lease_end_unix'],
        plan_path=str(output/'PLAN.json'), plan_sha256=native.sha(output/'PLAN.json'), resume=False, source_pins=cpu['source_pins'])
    if contained:
        config['device_containment'] = dict(minor=a100_device_minor(plan['gpu_uuid']),
            uid=os.getuid(), gid=os.getgid(), unit='orch-r136-native-'+uuid.uuid4().hex)
    write(output/'GUARD.json', config)
    return dict(guard_path=str(output/'GUARD.json'), plan_sha256=config['plan_sha256'], physical=physical,
        source_pins_sha256=native.digest(cpu['source_pins']), lease=lease, launch_attempted=False)


def math_provenance(physical):
    require(type(physical) is int and physical in (5, 6, 7), 'math_readonly_slots_only')
    root = MATH_ROOT/f'lane{physical}'
    plan = native.read(root/'PLAN.json')
    require(plan['schema'] == 'R122_C8_READ_ONLY_ELICITATION_V1'
        and plan['root'] == str(root) and plan['source_root'] == str(MATH_SOURCE)
        and plan['index'] == physical and plan['uuid'] == DEVICES[physical], 'math_exact_plan')
    require(plan['adapter_read_only'] is True and plan['optimizer_loaded'] is False
        and plan['optimizer_updates'] == 0, 'math_no_active_optimizer')
    require(native.sha(MATH_SOURCE/'gpu/orch_math_feedback_uptake_r122_a100.py') ==
        '2df864b51be86e9accba5c3ef22f5c55af4e30186b1ac59b23d2b264bc0ea9a0', 'math_reviewed_resident_source')
    require(plan['hard_end'] == 1790442300 and plan['lease_end'] == 1790463900
        and time.time()+900 < plan['hard_end'], 'math_original_lease')
    paths = [root, MATH_SOURCE]
    for key in ('source_manifest', 'cpu_tests', 'initial_carry', 'dev', 'exclusions',
            'lease_source', 'inventory', 'historical_cohort', 'historical_rows'):
        receipt = plan[key]
        require(native.sha(receipt['path']) == receipt['sha256'], 'math_bound_'+key)
        paths.append(Path(receipt['path']))
    require(native.read(plan['cpu_tests']['path'])['passed'] is True, 'math_original_CPU_pass')
    for name, digest in native.read(plan['source_manifest']['path']).items():
        path = MATH_SOURCE/name
        require(path.resolve().is_relative_to(MATH_SOURCE) and native.sha(path) == digest,
            'math_original_source')
    record = plan['record']
    require(record['cycle'] == 8 and record['historical_save_verified'] is True
        and record['optimizer_loaded_now'] is False and record['new_weight_updates'] == 0,
        'math_genuine_C8_readonly')
    adapter = record['adapter']
    require(adapter['base_sha256'] == native.BASE_SHA256, 'math_frozen_base')
    for name, digest in adapter['files']:
        require(Path(name).name == name and native.sha(Path(adapter['path'])/name) == digest,
            'math_saved_adapter')
    for key in ('optimizer', 'complete'):
        receipt = record[key]
        require(native.sha(receipt['path']) == receipt['sha256'], 'math_ancestral_'+key)
    after = Path(record['complete']['path']).with_name('AFTER.json')
    require(native.sha(after) == record['after_sha256'], 'math_ancestral_after')
    paths.extend([Path(adapter['path']), Path(record['optimizer']['path']).parent])
    return plan, paths


def validate_math_pair(request, plan):
    physical = request['physical']
    require(request['node'] == 'a100' and type(physical) is int and physical in (5, 6, 7),
        'math_readonly_slots_only')
    actor, supervisor = request['actor'], request['supervisor']
    require(actor['argv'] == [str(PYTHON), '-B', '-m', MATH_MODULE, 'resident', '--index', str(physical)]
        and supervisor['argv'] == ['python3', '-B', '-m', MATH_MODULE, 'guard', '--index', str(physical)],
        'math_exact_readonly_commands')
    require(actor['uid'] == supervisor['uid'] == os.getuid(), 'math_owned_pair')
    if 'orphan_recovery' in request:
        validate_math_orphan(request)
    else:
        require(actor['parent'] == supervisor['pid'], 'math_owned_pair')
    require(actor['cvd'] == [DEVICES[physical]] and supervisor['cvd'] in ([], ['']), 'math_exact_devices')
    launch = native.read(Path(plan['root'])/'LAUNCH.json')
    require(all(actor[key] == value for key, value in launch['identity'].items())
        and launch['plan']['sha256'] == native.sha(Path(plan['root'])/'PLAN.json'), 'math_original_launch')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
        and '2026-09-16' in request['gate']['builder_line'], 'dated_own_CPU_gate')
    require(1 <= request['wait_seconds'] <= 300, 'bounded_retirement_wait')


def validate_math_orphan(request):
    failure = BASE/'orch_r136_node1_classroom_20260916_attempt1/retire6_1'
    require(request['physical'] == 6 and request['actor']['parent'] == 1, 'exact_math6_orphan_only')
    proof = request['orphan_recovery']
    require(proof['path'] == str(failure/'ERROR.json') and native.sha(proof['path']) == proof['sha256'],
        'exact_orphan_failure_receipt')
    error = native.read(proof['path'])
    require(error['error_type'] == 'ValueError' and error['error'] == 'identity_drift_no_signal',
        'known_guard_first_failure_only')
    old = native.read(failure/'REQUEST.json')['request']
    require(request['actor'] == dict(old['actor'], parent=1)
        and request['supervisor'] == old['supervisor']
        and not Path(f"/proc/{old['supervisor']['pid']}").exists(), 'same_continuing_orphan_no_reset')
    preserved = native.read(failure/'PRESERVATION.json')
    require(native.sha(preserved['archive']['path']) == preserved['archive']['sha256'], 'old_orphan_archive_intact')
    require(native.read(failure/'BOUNDARY.json')['optimizer_updates'] == 0, 'old_orphan_boundary_readonly')


def math_frontier(root, initial_cycle, actor):
    root = Path(root)
    cursor = native.read(root/'CURSOR.json')
    following = cursor['next_cycle']
    require(type(following) is int and following > initial_cycle and following > 9,
        'math_prospective_saved_cursor')
    completed = following-9
    require(native.read(root/'COUNTERS.json') == dict(native=14*completed, parent=2*completed,
        optimizer_updates=0), 'math_no_reservation_beyond_cursor')
    require(not any(int(path.name[5:]) >= following for path in root.glob('cycle[0-9]*')),
        'math_no_next_cycle_work')
    expected = {f'native_{index:08d}.json' for index in range(1, 14*completed+1)}
    expected.update(f'parent_{index:08d}.json' for index in range(1, 2*completed+1))
    require({path.name for path in (root/'reservations').iterdir()} == expected, 'math_exact_reservations')
    calls = {path.name for path in (root/'calls').iterdir()}
    expected_calls = {f'CALL_{index:08d}{suffix}' for index in range(1, 14*completed+1)
        for suffix in ('.json', '.request.json')}
    require(calls == expected_calls, 'math_no_pending_or_extra_call')
    directory = root/f'cycle{following-1:06d}'
    carry = directory/'CARRY.json'
    require(cursor['carry'] == dict(path=str(carry), sha256=native.sha(carry)), 'math_exact_saved_carry')
    require(native.read(carry) == native.read(directory/'EXPERIENCE.json')[-1], 'math_carry_is_final_own_event')
    boundary = native.read(directory/'CONTEXT_BOUNDARY.json')
    require(boundary['cycle'] == following-1 and boundary['episodes'] == 2
        and boundary['weight_sleep'] is False and boundary['optimizer_updates'] == 0, 'math_complete_context_boundary')
    require(native.read(directory/'DEV_RESULT.json') == dict(status='COMPLETE', returncode=0), 'math_completed_readout')
    readout = native.read(directory/'DEV_LAUNCH.json')['identity']
    require(not preservation.alive(readout), 'math_readout_exited')
    require(not Path(f"/proc/{actor['pid']}/task/{actor['pid']}/children").read_text().strip(),
        'math_no_active_descendants')
    return dict(cursor=ref(root/'CURSOR.json'), carry=ref(carry), counters=ref(root/'COUNTERS.json'),
        context_boundary=ref(directory/'CONTEXT_BOUNDARY.json'), readout=ref(directory/'DEV_RESULT.json'),
        next_cycle=following, optimizer_loaded=False, optimizer_updates=0)


def retire_math(request, output):
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    plan, paths = math_provenance(request['physical'])
    validate_math_pair(request, plan)
    from gpu.orch_r125_continual_guard import validate
    config, new_plan = validate(request['scan_config'])
    require(new_plan['physical'] == request['physical'] and new_plan['gpu_uuid'] == plan['uuid'],
        'math_release_scan_same_slot')
    root, output = Path(plan['root']), Path(output)
    initial_cycle = native.read(root/'CURSOR.json')['next_cycle']
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', dict(request=request, old_plan=ref(root/'PLAN.json'), started_unix=time.time()))
    library = ctypes.CDLL(None, use_errno=True)
    watch = library.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    require(watch >= 0, 'inotify_required')
    descriptors, paused = {}, []
    pair = [('actor', request['actor'])]
    if 'orphan_recovery' not in request:
        pair.append(('supervisor', request['supervisor']))
    def interrupted(signum, frame):
        raise SystemExit('math_retirement_interrupted_resume_owners')
    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        require(library.inotify_add_watch(watch, os.fsencode(root), 0x8 | 0x80) >= 0, 'watch_exact_math_cursor')
        for label, process in pair:
            preservation.same(process)
            descriptors[label] = os.pidfd_open(process['pid'])
            preservation.same(process)
        deadline, attempts = time.monotonic()+request['wait_seconds'], 0
        while time.monotonic() < deadline:
            if not select.select([watch], [], [], 1)[0]:
                for label, process in pair:
                    preservation.same(process)
                continue
            if not boundary_event(os.read(watch, 65536), b'CURSOR.json'):
                continue
            attempts += 1
            try:
                for label, process in pair:
                    paused.append((label, process))
                    if label == 'actor':
                        signal.pidfd_send_signal(descriptors[label], signal.SIGSTOP)
                    preservation.pause(process, descriptors[label])
                boundary = math_frontier(root, initial_cycle, request['actor'])
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
                write(output/f'REJECTED_{attempts:04d}.json', dict(error=str(error), observed_unix=time.time()))
                for label, process in reversed(paused):
                    signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                paused.clear()
                continue
            write(output/'BOUNDARY.json', boundary)
            saved = archive_same_life(paths, output/'STATE.tar')
            require(math_frontier(root, initial_cycle, request['actor']) == boundary, 'math_frontier_still_saved')
            write(output/'PRESERVATION.json', dict(**saved, active_optimizer='ABSENT_READ_ONLY_C8',
                ancestral_optimizer='HASH_VERIFIED_AND_ARCHIVED', own_carry='EXACT_SAVED',
                live_generation_RNG='NOT_EXPORTED_NO_BITWISE_RESUME_CLAIM',
                parent_queue='SNAPSHOT_PLUS_UNCHANGED_ORIGINAL_PENDING_PUBLICATIONS', observed_unix=time.time()))
            for label, process in pair:
                preservation.same(process)
                signal.pidfd_send_signal(descriptors[label], signal.SIGTERM)
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
                require(bool(select.select([descriptors[label]], [], [], 30)[0]), 'math_owned_exit_no_KILL')
            paused.clear()
            write(output/'OLD_STOPPED.json', dict(boundary=ref(output/'BOUNDARY.json'),
                preservation=ref(output/'PRESERVATION.json'), stopped_unix=time.time()))
            report = scan(request['scan_config'], output/'RELEASE_SCAN.json')
            require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
                and report['gpu']['uuid'] == plan['uuid'], 'fresh_exclusive_release_required')
            receipt = dict(status='RELEASED', physical=request['physical'], gpu_uuid=plan['uuid'],
                actor=request['actor'], disabled_supervisor=request['supervisor'],
                preservation=ref(output/'PRESERVATION.json'), scan=ref(output/'RELEASE_SCAN.json'),
                finished_unix=time.time(), other_slots_touched=False)
            write(output/'RELEASED.json', receipt)
            return receipt
        write(output/'WAIT_EXPIRED.json', dict(status='NO_RELEASE', attempts=attempts, finished_unix=time.time()))
    except BaseException as error:
        write(output/'ERROR.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        for label, process in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[label], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        os.close(watch)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def gpu_descriptors():
    result = []
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            target = os.readlink(descriptor)
            if not target.startswith('/dev/nvidia'):
                continue
            metadata = descriptor.stat()
            require(stat.S_ISCHR(metadata.st_mode), 'GPU_descriptor_character_device')
            result.append(dict(fd=int(descriptor.name), path=target,
                major=os.major(metadata.st_rdev), minor=os.minor(metadata.st_rdev)))
        except FileNotFoundError:
            continue
    return sorted(result, key=lambda entry: entry['fd'])


def nvml_discovery_probe():
    before = gpu_descriptors()
    import torch
    require(not torch.cuda.is_initialized(), 'probe_must_not_initialize_CUDA')
    after_import = gpu_descriptors()
    count = torch.cuda._device_count_nvml()
    require(not torch.cuda.is_initialized(), 'NVML_only_no_CUDA_fallback')
    return dict(schema='R136_NVML_CPU_DISCOVERY_PROBE_V1', pid=os.getpid(),
        observed_unix=time.time(), cvd=os.environ.get('CUDA_VISIBLE_DEVICES'),
        before=before, after_import=after_import, after_nvml=gpu_descriptors(),
        nvml_visible_count=count, torch_cuda_initialized=False,
        torch_version=torch.__version__, torch_cuda_source=ref(Path(torch.cuda.__file__)),
        cgroup=Path('/proc/self/cgroup').read_text(),
        diagnostic_only=True, admission_receipt=False, gpu_model_calls=0)


def device_containment_command(physical, minor, uid, gid, unit, source, command, lifetime):
    require(type(physical) is int and physical in DEVICES, 'explicit_A100_physical')
    require(type(minor) is int and 0 <= minor <= 7, 'verified_GPU_minor')
    require(type(uid) is int and uid > 0 and type(gid) is int and gid > 0, 'nonroot_probe_identity')
    require(re.fullmatch(r'orch-r136-(nvml|native)-[a-f0-9]{32}', unit), 'unique_probe_unit')
    source = Path(source)
    require(source.is_absolute() and '..' not in source.parts, 'absolute_probe_source')
    require(type(lifetime) is int and lifetime > 0, 'bounded_containment_lifetime')
    properties = dict(User=str(uid), Group=str(gid), NoNewPrivileges='yes',
        DevicePolicy='strict', CapabilityBoundingSet='', AmbientCapabilities='',
        ProtectControlGroups='yes', RuntimeMaxSec=str(lifetime), TimeoutStopSec='5',
        KillMode='control-group', WorkingDirectory=str(source))
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        f'/dev/nvidia{minor} rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit='+unit,
        *['--property='+key+'='+value for key, value in properties.items()],
        '--property=DeviceAllow=', *['--property=DeviceAllow='+entry for entry in devices],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'HOME='+str(BASE),
        'CUDA_VISIBLE_DEVICES='+DEVICES[physical], 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+str(source), 'HF_HUB_OFFLINE=1', 'TRANSFORMERS_OFFLINE=1',
        'OMP_NUM_THREADS=1', 'MKL_NUM_THREADS=1', 'TOKENIZERS_PARALLELISM=false', *command]


def containment_probe_command(physical, minor, uid, gid, unit, source):
    require(re.fullmatch(r'orch-r136-nvml-[a-f0-9]{32}', unit), 'unique_probe_unit')
    return device_containment_command(physical, minor, uid, gid, unit, source,
        [str(PYTHON), '-B', '-m', 'gpu.orch_r136_node1_launcher', 'probe-nvml'], 30)


def a100_device_minor(gpu_uuid):
    require(gpu_uuid in DEVICES.values(), 'known_A100_UUID')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(len(matches) == 1 and 0 <= matches[0] <= 7, 'one_kernel_UUID_minor_mapping')
    node = Path('/dev/nvidia'+str(matches[0]))
    metadata = node.lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
        and os.minor(metadata.st_rdev) == matches[0], 'real_bound_GPU_character_device')
    return matches[0]


def verify_device_containment(config, plan):
    policy = config['device_containment']
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'nonroot_contained_identity')
    require(Path('/proc/self/cgroup').read_text().strip() ==
        '0::/system.slice/'+policy['unit']+'.service', 'exact_contained_service')
    require(a100_device_minor(plan['gpu_uuid']) == policy['minor'], 'unchanged_UUID_minor')
    require(not gpu_descriptors(), 'no_inherited_GPU_descriptors')
    denied = []
    for minor in range(8):
        if minor == policy['minor']:
            continue
        try:
            descriptor = os.open('/dev/nvidia'+str(minor), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(minor)
        else:
            os.close(descriptor)
            raise ValueError('foreign_GPU_not_denied_before_native_start')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'one_GPU_contained_environment')
    return dict(policy=policy, denied_foreign_minors=denied,
        checked_unix=time.time(), pid=os.getpid(), existing_processes_modified=False)


def contained_native(config_path):
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r133_code_feedback_guard import publish_launch, reap_owned_child
    config, plan = guard.validate(config_path)
    attempt = Path(config['attempt_dir'])
    proof = verify_device_containment(config, plan)
    write(attempt/'CONTAINMENT_VERIFIED.json', proof)
    admission = native.read(attempt/'ADMISSION.json')
    admitted = native.read(attempt/'ADMISSION_TIME.json')['verified_unix']
    require(admission['clear'] and admission['scanner_euid'] == 0 and not admission['blocking_reasons']
        and admission['gpu']['uuid'] == plan['gpu_uuid'] and 0 <= time.time()-admitted < 100,
        'fresh_global_admission_before_contained_native')
    remaining = int(plan['hard_end_unix']-time.time()-10)
    require(remaining > 10, 'time_for_native_load')
    command = ['timeout', '--signal=TERM', '--kill-after=5s', str(remaining)+'s', str(PYTHON),
        '-B', '-m', 'gpu.orch_r125_continual_guard', 'native', '--config', str(config_path)]
    process = None
    try:
        with (attempt/'NATIVE.log').open('x') as log:
            process = subprocess.Popen(command, cwd=plan['source_root'], stdin=subprocess.PIPE,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            identity = preservation.identity(process.pid)
            publish_launch(attempt/'LAUNCH.json', dict(pid=process.pid,
                parent_start_ticks=identity['start_ticks'], started_unix=time.time(),
                admission_verified_unix=admitted, admission_sha256=native.sha(attempt/'ADMISSION.json'),
                guard_sha256=native.sha(config_path), command_sha256=native.digest(command),
                plan_sha256=config['plan_sha256'], gpu_uuid=plan['gpu_uuid'],
                hard_end_unix=plan['hard_end_unix'], no_retry=True,
                containment_sha256=native.sha(attempt/'CONTAINMENT_VERIFIED.json')))
            process.stdin.write(b'LAUNCH_READY\n')
            process.stdin.close()
            status = process.wait()
        write(attempt/'EXIT.json', dict(exit_code=status, finished_unix=time.time(), no_retry=True))
        require(status == 0, 'contained_native_failed_no_retry')
    except BaseException:
        reap_owned_child(process)
        raise


def contained_supervise(config_path):
    from gpu import orch_r125_continual_guard as guard
    config, plan = guard.validate(config_path)
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    attempt = Path(config['attempt_dir'])
    (attempt/'DISPATCH_ONCE').mkdir()
    report = scan(config_path, attempt/'ADMISSION.json')
    require(report['clear'] and report['scanner_euid'] == 0 and not report['blocking_reasons']
        and report['gpu']['uuid'] == plan['gpu_uuid'], 'unchanged_global_exclusive_admission')
    write(attempt/'ADMISSION_TIME.json', dict(verified_unix=time.time()))
    policy = config['device_containment']
    command = device_containment_command(plan['physical'], policy['minor'], policy['uid'],
        policy['gid'], policy['unit'], plan['source_root'], [str(PYTHON), '-B', '-m',
            'gpu.orch_r136_node1_launcher', 'contained-native', '--config', str(config_path)],
        max(1, int(plan['hard_end_unix']-time.time())))
    write(attempt/'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt/'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'contained_service_failed_no_retry')


def validate_control_config(config_path):
    from gpu import orch_r139_continual_controls as controls
    config = native.read(config_path)
    require(config['schema'] == 'R139_NODE1_CONTROL_GUARD_V1' and config['resume'] is False,
        'new_control_only_no_resume')
    require(native.sha(config['plan_path']) == config['plan_sha256'], 'control_plan_bytes')
    plan = controls.validate_plan(native.read(config['plan_path']))
    controls.verify_gate(plan)
    require(type(plan['physical']) is int and plan['physical'] in (0, 1)
        and plan['gpu_uuid'] == DEVICES[plan['physical']]
        and plan['control']['mode'] == controls.MODES[plan['physical']], 'exact_A100_control_slot_mode')
    source = Path(plan['source_root']).resolve()
    require(source == Path(__file__).resolve().parents[1], 'control_executing_source')
    require({str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
        == config['source_pins'], 'control_entire_source_closure')
    require(socket.gethostname() == '[REDACTED_HOST]'
        and hashlib.sha256(socket.gethostname().encode()).hexdigest() == config['host_sha256'], 'control_A100_host')
    require(config['hard_end_unix'] == plan['hard_end_unix'] == 1790442300
        and plan['lease_end_unix'] == 1790463900 and time.time()+600 < plan['hard_end_unix'],
        'control_original_lease')
    require(native.sha(config['lease_path']) == config['lease_sha256'], 'control_lease_bytes')
    lease = native.read(config['lease_path'])
    require(lease['lease_end_unix'] == plan['lease_end_unix']
        and lease['hard_end_unix'] == plan['hard_end_unix'], 'control_lease_binding')
    require(native.sha(config['allocation_path']) == config['allocation_sha256'], 'control_allocation_bytes')
    allocation = native.read(config['allocation_path'])
    require(allocation['plan_sha256'] == config['plan_sha256'] and allocation['cpu_tests_passed'] is True
        and allocation['physical'] == plan['physical'] and allocation['gpu_uuid'] == plan['gpu_uuid']
        and allocation['base_commit'] == 'de1fc4b779e939a1082c54c341bef8a6a6497512',
        'control_original_published_allocation')
    attempt = Path(config['attempt_dir'])
    require(attempt.is_absolute() and not attempt.resolve().is_relative_to(source), 'control_attempt_outside_source')
    return config, plan


def control_scan(config_path):
    config, plan = validate_control_config(config_path)
    require(os.geteuid() == 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'privileged_CPU_scan')
    from gpu import orch_rich_hot_a100_minor_scan as minor
    from gpu import orch_r111_route_admission as admission
    def allocation(index):
        require(index == plan['physical'], 'only_allocated_device')
    minor.pinned.policy = SimpleNamespace(HOST_SHA=config['host_sha256'],
        DEVICES={plan['physical']:plan['gpu_uuid']}, require=require, allocation=allocation)
    service = Path(config['attempt_dir'])/'SERVICE_IDENTITY.json'
    if not service.exists():
        minor.pinned.service(service)
    return admission.scan(plan['physical'], service)


def control_admission_receipt(config, plan, receipt, config_path):
    require(receipt['config_sha256'] == native.sha(config_path)
        and receipt['plan_sha256'] == config['plan_sha256'], 'control_admitted_exact_plan')
    require(0 <= time.time()-receipt['admitted_unix'] <= 120, 'fresh_control_admission')
    require(native.sha(receipt['scan']['path']) == receipt['scan']['sha256'], 'control_admission_bytes')
    report = native.read(receipt['scan']['path'])
    require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
        and report['gpu']['uuid'] == plan['gpu_uuid'], 'unchanged_control_admission')


def control_native(config_path):
    from gpu import orch_r139_continual_controls as controls
    config, plan = validate_control_config(config_path)
    attempt = Path(config['attempt_dir'])
    require((attempt/'DISPATCH_ONCE').is_dir(), 'one_control_dispatch')
    control_admission_receipt(config, plan, native.read(attempt/'ADMITTED.json'), config_path)
    proof = verify_device_containment(config, plan)
    write(attempt/'CONTAINMENT_VERIFIED.json', proof)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'], 'control_single_GPU')
    os.environ['R125_ADMISSION_PLAN_SHA256'] = config['plan_sha256']
    write(attempt/'NATIVE_LAUNCH.json', dict(identity=preservation.identity(os.getpid()),
        plan_sha256=config['plan_sha256'], config_sha256=native.sha(config_path),
        containment=ref(attempt/'CONTAINMENT_VERIFIED.json'), started_unix=time.time(),
        status='DISPATCHED_NOT_LOADED', resume=False))
    controls.run(config['plan_path'])


def control_supervise(config_path):
    config, plan = validate_control_config(config_path)
    attempt = Path(config['attempt_dir'])
    (attempt/'DISPATCH_ONCE').mkdir()
    command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
        'PYTHONPATH='+plan['source_root'], str(PYTHON), '-B', '-m', 'gpu.orch_r136_node1_launcher',
        'control-scan', '--config', str(config_path)]
    report = json.loads(subprocess.check_output(command, text=True, timeout=100))
    write(attempt/'ADMISSION.json', report)
    receipt = dict(config_sha256=native.sha(config_path), plan_sha256=config['plan_sha256'],
        admitted_unix=time.time(), scan=ref(attempt/'ADMISSION.json'))
    control_admission_receipt(config, plan, receipt, config_path)
    write(attempt/'ADMITTED.json', receipt)
    policy = config['device_containment']
    command = device_containment_command(plan['physical'], policy['minor'], policy['uid'], policy['gid'],
        policy['unit'], plan['source_root'], [str(PYTHON), '-B', '-m', 'gpu.orch_r136_node1_launcher',
            'control-native', '--config', str(config_path)], max(1, int(plan['hard_end_unix']-time.time())))
    write(attempt/'CONTAINED_COMMAND.json', dict(command=command, started_unix=time.time()))
    result = subprocess.run(command, check=False)
    write(attempt/'SERVICE_EXIT.json', dict(returncode=result.returncode, finished_unix=time.time()))
    require(result.returncode == 0, 'control_failed_preserved_no_retry')


def consumer_provenance(request):
    require(request['node'] == 'a100' and type(request['physical']) is int
        and request['physical'] in (0, 1), 'consumer_slots_only')
    arm = ('FULL', 'CONTROL')[request['physical']]
    require(request['arm'] == arm, 'consumer_slot_arm')
    supervisor = request['supervisor']
    require(supervisor['argv'] == [str(PYTHON), '-B', '-u', str(CONSUMER_ROOT/'orch_r132_gen7_feed_registration.py'),
        'activate', '--root', str(CONSUMER_ROOT), '--arm', arm] and supervisor['uid'] == os.getuid()
        and supervisor['cvd'] in ([], ['']), 'exact_consumer_CPU_supervisor')
    require(native.sha(CONSUMER_ROOT/'orch_r132_gen7_feed_registration.py') ==
        'd44d79d171bd5c169367c1d34dfc01d240d7f91edadc18e4ad4b936a09c29832'
        and native.sha(CONSUMER_ROOT/'orch_r119_l1_c3_consumer.py') ==
        '4ffedb907e39313cbaf1ac3a56f163c82c6a646db648781f92addb218f6a29f5', 'reviewed_consumer_loop')
    for name, checksum in native.read(CONSUMER_ROOT/'R132_SOURCE_PINS.json').items():
        require(Path(name).name == name and native.sha(CONSUMER_ROOT/name) == checksum, 'consumer_frozen_sources')
    campaign = native.read(CONSUMER_ROOT/'CAMPAIGN.json')
    require(campaign['slots'] == dict(FULL=0, CONTROL=1) and campaign['uuid_by_index'] == list(DEVICES.values())
        and campaign['hard_deadline_unix'] == 1790442300 and campaign['lease_end_unix'] == 1790463900
        and campaign['experiment'] == 'R132_GEN7_C4', 'consumer_original_experiment_and_wall')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
        and '2026-09-16' in request['gate']['builder_line'] and 1 <= request['wait_seconds'] <= 900,
        'consumer_bounded_CPU_gate')
    start = native.read(CONSUMER_ROOT/f'START_{arm}.json')['identity']
    require(all(supervisor[key] == value for key, value in start.items()), 'original_consumer_owner')
    return campaign


def consumer_frontier(root, arm, supervisor, minimum_segment):
    root = Path(root)
    require(not Path(f"/proc/{supervisor['pid']}/task/{supervisor['pid']}/children").read_text().strip(),
        'consumer_no_active_train_readout_or_scan_child')
    stages = sorted((root/arm).glob('segment[0-9]*'), key=lambda path: int(path.name[7:]))
    require(bool(stages), 'consumer_existing_stages')
    stage = stages[-1]
    segment = int(stage.name[7:])
    require(segment >= minimum_segment, 'consumer_new_boundary')
    paired_path = stage/'PAIRED_COMPLETE.json'
    paired = native.read(paired_path)
    require(paired['binding_sha256'] == native.sha(stage/'BINDING.json'), 'consumer_paired_stage_binding')
    checkpoint = Path(paired['checkpoint'])
    require(checkpoint.is_relative_to(stage/'fit'/arm/'checkpoints'), 'consumer_checkpoint_local')
    complete_path = stage/'fit'/arm/f'segment{segment:03d}'/'COMPLETE.json'
    complete = native.read(complete_path)
    require(complete['checkpoint'] == str(checkpoint) and complete['commit_sha256'] == native.sha(checkpoint/'COMMIT.json'),
        'consumer_latest_train_complete')
    commit = native.read(checkpoint/'COMMIT.json')
    metadata = commit['metadata']
    require(metadata['arm'] == arm and metadata['optimizer_preserved'] is True and metadata['rng_per_rank'] is True
        and metadata['original_history_unchanged'] is True and metadata['update'] == complete['update']
        and metadata['lifetime']['hard_deadline_unix'] == 1790442300, 'consumer_exact_optimizer_frontier')
    require({'optimizer.pt', 'rank0.pt', 'rank1.pt', 'adapter/adapter_model.safetensors'} <= commit['files'].keys(),
        'consumer_all_saved_states_required')
    for name, checksum in commit['files'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and native.sha(checkpoint/name) == checksum, 'consumer_saved_state_bytes')
    for phase, condition in (('train', 'None'), ('readout', 'ON'), ('readout', 'OFF')):
        require(native.read(stage/f'{phase}_{condition}_EXIT.json')['returncode'] == 0, 'consumer_finished_phases')
        launch = native.read(stage/f'{phase}_{condition}_LAUNCH.json')
        require(launch['binding_sha256'] == paired['binding_sha256']
            and not preservation.alive(launch['identity']), 'consumer_phase_process_exited')
    require(set(paired['readouts']) == {'ON', 'OFF'}, 'consumer_both_readouts')
    for receipt in paired['readouts'].values():
        require(Path(receipt['path']).is_relative_to(stage/'fit'/arm)
            and native.sha(receipt['path']) == receipt['sha256'], 'consumer_paired_readout_bytes')
    return dict(segment=segment, checkpoint=str(checkpoint), commit=ref(checkpoint/'COMMIT.json'),
        optimizer=ref(checkpoint/'optimizer.pt'), rank0_rng=ref(checkpoint/'rank0.pt'),
        rank1_rng=ref(checkpoint/'rank1.pt'), update=metadata['update'], paired=ref(paired_path),
        complete=ref(complete_path), adapter_state_sha256=metadata['adapter']['state_sha256'],
        carry='NO_GENERATION_CARRY; FULL_TRAINING_STATE_AND_FEED_BINDINGS_PRESERVED')


def archive_consumer(paths, destination, campaign):
    allowed = {Path(record['path'])/'ENCODED.json' for record in campaign['cohorts'].values()}
    allowed.add(Path(campaign['held_path']))
    files, links = set(), {}
    for root in map(Path, paths):
        require(not root.is_symlink(), 'consumer_archive_root_not_link')
        for path in ([root] if root.is_file() else root.rglob('*')):
            if path.is_symlink():
                target = path.readlink()
                require(target in allowed and path.is_file() and not target.is_symlink(),
                    'consumer_only_bound_dataset_links')
                links[str(path)] = str(target)
            if path.is_file():
                files.add(path)
    manifest = {str(path): ref(path) for path in sorted(files)}
    space = os.statvfs(destination.parent)
    require(space.f_bavail*space.f_frsize > sum(item['bytes'] for item in manifest.values())*2+1024**3,
        'consumer_archive_headroom')
    with tarfile.open(destination, 'x', dereference=True) as archive:
        for path in sorted(files):
            archive.add(path, arcname=str(path).lstrip('/'), recursive=False)
    with destination.open('rb') as stream:
        os.fsync(stream.fileno())
    with tarfile.open(destination, 'r') as archive:
        members = archive.getmembers()
        require(len(members) == len(manifest), 'consumer_archive_member_count')
        for member in members:
            require(member.isfile() and '/'+member.name in manifest, 'consumer_archive_regular_entries')
            checksum = hashlib.sha256()
            with archive.extractfile(member) as stream:
                for block in iter(lambda: stream.read(1024*1024), b''):
                    checksum.update(block)
            require(checksum.hexdigest() == manifest['/'+member.name]['sha256'], 'consumer_archive_exact_bytes')
    require(all(native.sha(path) == receipt['sha256'] for path, receipt in manifest.items())
        and all(Path(path).is_symlink() and str(Path(path).readlink()) == target for path, target in links.items()),
        'consumer_original_sources_unchanged')
    destination.chmod(0o444)
    return dict(archive=ref(destination), files=manifest, original_symlink_targets=links,
        archive_links_materialized_as_verified_regular_bytes=True)


def retire_consumer(request, output):
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    campaign = consumer_provenance(request)
    config, plan = validate_control_config(request['scan_config'])
    require(plan['physical'] == request['physical'], 'consumer_release_same_control_slot')
    arm, supervisor = request['arm'], request['supervisor']
    stages = sorted((CONSUMER_ROOT/arm).glob('segment[0-9]*'), key=lambda path: int(path.name[7:]))
    minimum = int(stages[-1].name[7:])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', dict(request=request, minimum_segment=minimum, started_unix=time.time()))
    preservation.same(supervisor)
    descriptor = os.pidfd_open(supervisor['pid'])
    paused = False
    def interrupted(signum, frame):
        raise SystemExit('consumer_observer_interrupted_resume_supervisor')
    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        deadline, attempts, last_candidate = time.monotonic()+request['wait_seconds'], 0, None
        while time.monotonic() < deadline:
            preservation.same(supervisor)
            stages = sorted((CONSUMER_ROOT/arm).glob('segment[0-9]*'), key=lambda path: int(path.name[7:]))
            candidate = stages[-1]/'PAIRED_COMPLETE.json'
            if candidate == last_candidate or not candidate.exists():
                time.sleep(0.01)
                continue
            attempts += 1
            last_candidate = candidate
            try:
                paused = True
                preservation.pause(supervisor, descriptor)
                boundary = consumer_frontier(CONSUMER_ROOT, arm, supervisor, minimum)
            except (ValueError, FileNotFoundError, json.JSONDecodeError) as error:
                write(output/f'REJECTED_{attempts:04d}.json', dict(error=str(error), observed_unix=time.time()))
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
                paused = False
                continue
            write(output/'BOUNDARY.json', boundary)
            paths = [CONSUMER_ROOT/arm]+[path for path in CONSUMER_ROOT.iterdir()
                if path.is_file() and path.suffix not in ('.lock', '.log')
                and not path.name.startswith('HEARTBEAT_')]
            saved = archive_consumer(paths, output/'STATE.tar', campaign)
            require(consumer_frontier(CONSUMER_ROOT, arm, supervisor, minimum) == boundary, 'consumer_boundary_unchanged')
            write(output/'PRESERVATION.json', dict(**saved, optimizer_and_all_rank_rng='EXACT_SAVED',
                original_tree_preserved=True, observed_unix=time.time()))
            preservation.same(supervisor)
            signal.pidfd_send_signal(descriptor, signal.SIGTERM)
            signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            require(bool(select.select([descriptor], [], [], 30)[0]), 'consumer_owner_exit_no_KILL')
            paused = False
            write(output/'OLD_STOPPED.json', dict(boundary=ref(output/'BOUNDARY.json'),
                preservation=ref(output/'PRESERVATION.json'), stopped_unix=time.time()))
            command = ['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=', 'PYTHONDONTWRITEBYTECODE=1',
                'PYTHONPATH='+plan['source_root'], str(PYTHON), '-B', '-m', 'gpu.orch_r136_node1_launcher',
                'control-scan', '--config', request['scan_config']]
            report = json.loads(subprocess.check_output(command, text=True, timeout=100))
            write(output/'RELEASE_SCAN.json', report)
            require(report['clear'] is True and report['scanner_euid'] == 0 and not report['blocking_reasons']
                and report['gpu']['uuid'] == plan['gpu_uuid'], 'fresh_control_release_required')
            receipt = dict(status='RELEASED', physical=request['physical'], gpu_uuid=plan['gpu_uuid'],
                disabled_supervisor=supervisor, preservation=ref(output/'PRESERVATION.json'),
                scan=ref(output/'RELEASE_SCAN.json'), finished_unix=time.time(), no_training_process_signalled=True)
            write(output/'RELEASED.json', receipt)
            return receipt
        write(output/'WAIT_EXPIRED.json', dict(status='NO_RELEASE', attempts=attempts, finished_unix=time.time()))
    except BaseException as error:
        write(output/'ERROR.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        if paused:
            try:
                signal.pidfd_send_signal(descriptor, signal.SIGCONT)
            except ProcessLookupError:
                pass
        os.close(descriptor)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


def same_life_plan(old_plan, source):
    plan = deepcopy(old_plan)
    plan['source_root'] = str(source)
    if plan.get('startup_context'):
        relative = Path(old_plan['startup_context']['path']).relative_to(old_plan['source_root'])
        plan['startup_context']['path'] = str(Path(source)/relative)
        require(native.sha(plan['startup_context']['path']) == old_plan['startup_context']['sha256'],
            'identical_startup_bytes')
    require(native.experiment_binding(plan) == native.experiment_binding(old_plan), 'same_life_experiment')
    return native.validate_plan(plan)


def stage_contained_resume(old_config_path, source, output, cpu_receipt):
    old_config_path, source, output, cpu_receipt = map(Path, (old_config_path, source, output, cpu_receipt))
    old_config = native.read(old_config_path)
    old_plan = native.read(old_config['plan_path'])
    require(native.sha(old_config['plan_path']) == old_config['plan_sha256'], 'old_bound_plan')
    require(old_plan['physical'] == 2 and old_plan['gpu_uuid'] == DEVICES[2], 'first_A1002_handoff_only')
    for relative, checksum in old_config['source_pins'].items():
        require(native.sha(Path(old_plan['source_root'])/relative) == checksum, 'old_source_unchanged')
    cpu = native.read(cpu_receipt)
    actual = {str(path.relative_to(source)): native.sha(path) for path in source.rglob('*.py')}
    require(cpu['passed'] is True and cpu['source_pins'] == actual, 'tested_entire_new_source')
    changed = {relative for relative in set(actual) | set(old_config['source_pins'])
        if actual.get(relative) != old_config['source_pins'].get(relative)}
    require(changed <= {'gpu/orch_r136_node1_launcher.py', 'tests/test_orch_r136_node1_launcher.py'},
        'operator_only_runtime_bytes_unchanged')
    require(source.is_absolute() and source != Path(old_plan['source_root']) and output.is_absolute(),
        'new_absolute_operator_source_and_attempt')
    plan = same_life_plan(old_plan, source)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'PLAN.json', plan)
    allocation = dict(native.read(old_config['allocation_path']), plan_sha256=native.sha(output/'PLAN.json'),
        declared_unix=time.time(), checkpoint_resume=True, cpu_receipt_path=str(cpu_receipt),
        cpu_receipt_sha256=native.sha(cpu_receipt), current_CPU_gate_pushed=False,
        builder_entry='R136 same-life device containment; original published allocation, own dated CPU gate')
    write(output/'ALLOCATION.json', allocation)
    config = dict(old_config, plan_path=str(output/'PLAN.json'), plan_sha256=native.sha(output/'PLAN.json'),
        allocation_path=str(output/'ALLOCATION.json'), allocation_sha256=native.sha(output/'ALLOCATION.json'),
        attempt_dir=str(output), resume=True, source_pins=actual,
        device_containment=dict(minor=a100_device_minor(plan['gpu_uuid']), uid=os.getuid(), gid=os.getgid(),
            unit='orch-r136-native-'+uuid.uuid4().hex))
    write(output/'GUARD.json', config)
    write(output/'SAME_LIFE.json', dict(old_config=ref(old_config_path), old_plan=ref(old_config['plan_path']),
        new_plan=ref(output/'PLAN.json'), new_source_pins_sha256=native.digest(actual),
        reset=False, lease_extended=False, runtime_changed=False, parent_untouched=True,
        changed_source_files=sorted(changed), cpu_receipt=ref(cpu_receipt)))
    return dict(guard_path=str(output/'GUARD.json'), plan_sha256=config['plan_sha256'])


def validate_handoff_processes(request, old_config, old_plan, launch):
    require(old_plan['physical'] == 2 and old_plan['gpu_uuid'] == DEVICES[2], 'A1002_only_saved_handoff')
    require(type(request['wait_seconds']) is int and 1 <= request['wait_seconds'] <= 1200,
        'bounded_handoff_wait')
    path = request['old_config']['path']
    actor, timer, supervisor = (request[name] for name in ('actor', 'timer', 'supervisor'))
    prefix = [str(PYTHON), '-B', '-m', 'gpu.orch_r125_continual_guard']
    require(actor['argv'] == prefix+['native', '--config', path]
        and supervisor['argv'] == prefix+['supervise', '--config', path], 'exact_old_native_guard_pair')
    require(timer['argv'][:3] == ['timeout', '--signal=TERM', '--kill-after=5s']
        and len(timer['argv']) == 11 and re.fullmatch(r'[1-9][0-9]*s', timer['argv'][3])
        and timer['argv'][4:] == actor['argv'], 'exact_old_timeout_command')
    require(actor['parent'] == timer['pid'] and timer['parent'] == supervisor['pid']
        and timer['pid'] == launch['pid'] and timer['start_ticks'] == launch['parent_start_ticks'],
        'exact_owned_native_ancestry')
    require(all(process['uid'] == os.getuid() for process in (actor, timer, supervisor))
        and actor['cvd'] == timer['cvd'] == [DEVICES[2]] and supervisor['cvd'] == [''],
        'owned_single_device_processes')
    require(launch['guard_sha256'] == request['old_config']['sha256']
        and launch['plan_sha256'] == old_config['plan_sha256'], 'original_launch_binding')


def verify_stream_snapshot(snapshot, original, expected_sha256):
    from gpu.orch_r125_stream_journal import StreamJournal
    original_inbox = SimpleNamespace(inbox=Path(original)/'inbox')
    class SnapshotJournal(StreamJournal):
        def _inbox_event(self, message, path, source_sha256):
            return StreamJournal._inbox_event(original_inbox, message, path, source_sha256)
    with SnapshotJournal(snapshot, create=False) as journal:
        latest = journal.latest_checkpoint()
        require(latest is not None and latest['expected_sha256'] == expected_sha256,
            'full_journal_chain_verified_before_stop')
    return latest


def archive_same_life(paths, destination):
    files = set()
    for root in map(Path, paths):
        require(not root.is_symlink(), 'same_life_archive_root_symlink')
        for path in ([root] if root.is_file() else root.rglob('*')):
            require(not path.is_symlink(), 'same_life_archive_symlink')
            if path.is_file():
                files.add(path)
    files = sorted(files)
    required = sum(path.stat().st_size for path in files)
    space = os.statvfs(destination.parent)
    require(space.f_bavail*space.f_frsize > required*2+1024**3, 'same_life_archive_headroom')
    manifest = {str(path): ref(path) for path in files}
    with tarfile.open(destination, 'x', dereference=True) as archive:
        for path in files:
            archive.add(path, arcname=str(path).lstrip('/'), recursive=False)
    with destination.open('rb') as stream:
        os.fsync(stream.fileno())
    with tarfile.open(destination, 'r') as archive:
        members = archive.getmembers()
        require(len(members) == len(manifest), 'same_life_archive_member_count')
        for entry in members:
            require(entry.isfile() and '/'+entry.name in manifest, 'same_life_archive_regular_members')
            digest = hashlib.sha256()
            with archive.extractfile(entry) as stream:
                for block in iter(lambda: stream.read(1024*1024), b''):
                    digest.update(block)
            require(digest.hexdigest() == manifest['/'+entry.name]['sha256'], 'same_life_archive_member_hash')
    require(all(native.sha(path) == receipt['sha256'] for path, receipt in manifest.items()),
        'same_life_source_changed_during_archive')
    destination.chmod(0o444)
    return dict(archive=ref(destination), files=manifest, hardlinks_preserved_as_regular_bytes=True)


def handoff_contained(request, output):
    from gpu import orch_r125_continual_guard as guard
    from gpu.orch_r131_saved_boundary_handoff import sleep_boundary, readout_started
    require(socket.gethostname() == '[REDACTED_HOST]', 'A100_host_only')
    old_reference = request['old_config']
    require(native.sha(old_reference['path']) == old_reference['sha256'], 'unchanged_original_guard')
    old_config = native.read(old_reference['path'])
    require(native.sha(old_config['plan_path']) == old_config['plan_sha256'], 'unchanged_original_plan')
    old_plan = native.read(old_config['plan_path'])
    launch = native.read(Path(old_config['attempt_dir'])/'LAUNCH.json')
    validate_handoff_processes(request, old_config, old_plan, launch)
    config, plan = guard.validate(request['new_config'])
    require(config['resume'] is True and plan == same_life_plan(old_plan, plan['source_root']),
        'operator_only_same_life_plan')
    same_life = native.read(Path(config['attempt_dir'])/'SAME_LIFE.json')
    cpu = same_life['cpu_receipt']
    require(native.sha(cpu['path']) == cpu['sha256'] and native.read(cpu['path'])['passed'] is True,
        'bound_handoff_CPU_receipt')
    require(request['gate']['cpu_passed'] is True and '[Builder]' in request['gate']['builder_line']
        and '2026-09-16' in request['gate']['builder_line'], 'dated_handoff_CPU_gate')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output/'REQUEST.json', request)
    root = Path(plan['root'])
    deadline = min(time.monotonic()+request['wait_seconds'],
        time.monotonic()+plan['hard_end_unix']-time.time()-120)
    pair = [(name, request[name]) for name in ('supervisor', 'timer', 'actor')]
    descriptors, paused = {}, []
    def interrupted(signum, frame):
        raise SystemExit('handoff_interrupted_resume_exact_paused_processes')
    handlers = {signum: signal.signal(signum, interrupted) for signum in (signal.SIGTERM, signal.SIGHUP)}
    try:
        for name, process in pair:
            preservation.same(process)
            descriptors[name] = os.pidfd_open(process['pid'])
            preservation.same(process)
        while time.monotonic() < deadline:
            boundary = sleep_boundary(root)
            if boundary is None or not readout_started(root, boundary['cycle'],
                    plan.get('readout_revision', 1), request['timer']['pid']):
                time.sleep(.5)
                continue
            for name, process in pair:
                paused.append((name, process))
                preservation.pause(process, descriptors[name])
            checked = sleep_boundary(root)
            if checked is None or checked['record_sha256'] != boundary['record_sha256']:
                for name, process in reversed(paused):
                    signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                paused.clear()
                continue
            readout = root/'readouts'/native.readout_name(plan, boundary['cycle'])
            complete = readout/'COMPLETE.json'
            while time.monotonic() < deadline and not complete.exists():
                time.sleep(.5)
            require(complete.exists() and native.read(complete)['status'] == 'COMPLETE',
                'finished_fresh_readout_before_handoff')
            readout_pid = native.read(complete)['pid']
            while time.monotonic() < deadline:
                process_path = Path('/proc', str(readout_pid), 'stat')
                if not process_path.exists() or process_path.read_text().rsplit(')', 1)[1].split()[0] == 'Z':
                    break
                time.sleep(.1)
            else:
                raise ValueError('fresh_readout_process_not_exited')
            require(sleep_boundary(root) == boundary, 'saved_frontier_after_readout')
            stream = native.ContinualStream.restore(dict(state=boundary['state'], sha256=boundary['state_sha256']),
                expected_sha256=boundary['state_sha256'])
            native.verify_experiment_resume(plan, stream.experiment)
            checkpoint_path = root/'checkpoints'/f"sleep_{boundary['cycle']:06d}"/'COMMIT.json'
            checkpoint = native.read(checkpoint_path)
            native.NativeChild.verify_checkpoint(checkpoint)
            require(native.digest(checkpoint['checkpoint_sha256']) == stream.model_state_sha256
                and checkpoint.get('experiment') == stream.experiment
                and stream.deadline_unix == plan['hard_end_unix'], 'exact_saved_model_RNG_stream_and_wall')
            write(output/'BOUNDARY.json', dict(record=ref(boundary['path']),
                state_sha256=boundary['state_sha256'], checkpoint=ref(checkpoint_path),
                readout=ref(complete), cycle=boundary['cycle'], optimizer_steps=checkpoint['optimizer_steps']))
            saved = archive_same_life([root/'stream', root/'checkpoints', root/'readouts',
                old_reference['path'], old_config['plan_path'], old_config['lease_path'],
                Path(old_plan['source_root'])], output/'STATE.tar')
            require(sleep_boundary(root) == boundary, 'saved_frontier_after_archive')
            write(output/'PRESERVATION.json', dict(**saved, reset=False, optimizer_and_rng='EXACT_SAVED',
                same_root_and_inbox=True, parent_kept_running=True, observed_unix=time.time()))
            from gpu.orch_r125_stream_journal import StreamJournal
            shutil.copytree(root/'stream', output/'STREAM_VERIFY')
            verify_stream_snapshot(output/'STREAM_VERIFY', root/'stream', boundary['state_sha256'])
            require(sleep_boundary(root) == boundary, 'saved_frontier_before_stop')
            for name, process in reversed(pair):
                if preservation.alive(process):
                    preservation.same(process)
                    signal.pidfd_send_signal(descriptors[name], signal.SIGTERM)
                    signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
                    require(bool(select.select([descriptors[name]], [], [], 30)[0]), 'saved_owner_exit_no_KILL')
            paused.clear()
            write(output/'OLD_STOPPED.json', dict(old_actor=request['actor'], boundary=ref(output/'BOUNDARY.json'),
                preserved=ref(output/'PRESERVATION.json'), reset=False, stopped_unix=time.time()))
            with StreamJournal(root/'stream', create=False) as journal:
                latest = journal.latest_checkpoint()
                require(latest['expected_sha256'] == boundary['state_sha256'], 'same_authoritative_resume_state')
            command = [str(PYTHON), '-B', '-m', 'gpu.orch_r136_node1_launcher',
                'contained-supervise', '--config', request['new_config']]
            with (output/'SUPERVISOR.log').open('x') as log:
                process = subprocess.Popen(command, cwd=plan['source_root'],
                    env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=plan['source_root'],
                        PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            receipt = dict(status='HANDOFF_DISPATCHED_NOT_LOADED', supervisor_pid=process.pid,
                command_sha256=native.digest(command), dispatched_unix=time.time(), reset=False,
                new_config=ref(request['new_config']), boundary=ref(output/'BOUNDARY.json'))
            write(output/'HANDOFF.json', receipt)
            return receipt
        write(output/'WAIT_EXPIRED.json', dict(status='NO_HANDOFF', finished_unix=time.time()))
    except BaseException as error:
        write(output/'ERROR.json', dict(error_type=type(error).__name__, error=str(error), finished_unix=time.time()))
        raise
    finally:
        for name, process in reversed(paused):
            try:
                signal.pidfd_send_signal(descriptors[name], signal.SIGCONT)
            except ProcessLookupError:
                pass
        for descriptor in descriptors.values():
            os.close(descriptor)
        for signum, handler in handlers.items():
            signal.signal(signum, handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    commands.add_parser('probe-nvml')
    for name in ('contained-native', 'contained-supervise', 'control-native', 'control-supervise', 'control-scan'):
        command_parser = commands.add_parser(name)
        command_parser.add_argument('--config', type=Path, required=True)
    retirement = commands.add_parser('retire-generation')
    retirement.add_argument('--request', type=Path, required=True)
    retirement.add_argument('--output', type=Path, required=True)
    math_retirement = commands.add_parser('retire-math')
    math_retirement.add_argument('--request', type=Path, required=True)
    math_retirement.add_argument('--output', type=Path, required=True)
    consumer_retirement = commands.add_parser('retire-consumer')
    consumer_retirement.add_argument('--request', type=Path, required=True)
    consumer_retirement.add_argument('--output', type=Path, required=True)
    handoff = commands.add_parser('handoff-contained')
    handoff.add_argument('--request', type=Path, required=True)
    handoff.add_argument('--output', type=Path, required=True)
    staging = commands.add_parser('stage')
    for name in ('source', 'output', 'startup', 'cpu-receipt'):
        staging.add_argument('--'+name, type=Path, required=True)
    staging.add_argument('--physical', type=int, required=True)
    staging.add_argument('--base-commit', required=True)
    staging.add_argument('--contained', action='store_true')
    args = vars(parser.parse_args())
    action = args.pop('action')
    if action == 'stage':
        print(json.dumps(stage(**args), sort_keys=True))
    elif action == 'probe-nvml':
        print(json.dumps(nvml_discovery_probe(), sort_keys=True))
    elif action == 'contained-native':
        contained_native(args['config'])
    elif action == 'contained-supervise':
        contained_supervise(args['config'])
    elif action == 'control-native':
        control_native(args['config'])
    elif action == 'control-supervise':
        control_supervise(args['config'])
    elif action == 'control-scan':
        print(json.dumps(control_scan(args['config']), sort_keys=True))
    elif action == 'handoff-contained':
        print(json.dumps(handoff_contained(native.read(args['request']), args['output']), sort_keys=True))
    elif action == 'retire-math':
        print(json.dumps(retire_math(native.read(args['request']), args['output']), sort_keys=True))
    elif action == 'retire-consumer':
        print(json.dumps(retire_consumer(native.read(args['request']), args['output']), sort_keys=True))
    else:
        print(json.dumps(retire_generation(native.read(args['request']), args['output']), sort_keys=True))
