"""Main-GO-only, single-actor retirement of node5's old episodic lanes."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import threading
import time

from gpu import orch_r139_route_astra_handoff as route
from gpu import orch_r140_grid_continuation as grid


BASE = Path('/localhome/local-rohing')
HOST = 'ipp2-ovx-p1-10'
BOOT = '2c05ffec-1b4c-472f-9688-2a37543a6f4a'
HARD_END = 1789596240
COHORT_HARD_END = 1789617240
LEASE_END = 1789617840
GENERIC_LEASE_SHA256 = '12e187a3237d6c167d91c4abaae9e6ef671e096d827c9ed68a662aa465d51049'
ARM_PHYSICALS = {'parented_learning': 0, 'parented_frozen': 4, 'unparented_learning': 3}
PHYSICALS = (0, 3, 4)
PROTECTED = (1, 2, 5, 6, 7)
F4_LIMITATION = ('Old frozen episodic elicitation, not a protected continual child. '
    'Its source NEVER captured current sampling RNG. Exact F4 continuation is '
    'not claimed or possible; R150 is a NEW matched life. Preserve all existing '
    'files, latest available adapter/checkpoint, carry, history and accounting; '
    'do not fabricate RNG, delete, reset or replay saved artifacts.')
ROUTE_SOURCE = BASE / 'orch_r121_route_independent_20260915_v2/source/gpu/orch_r121_route_independent.py'
F1_STAGE = BASE / 'orch_r139_F1_astra_handoff_20260916_attempt3'
F4_SOURCE = BASE / 'orch_r140_F4_continuation_source_v1/gpu/orch_r140_grid_continuation.py'
TIMER_SOURCE = BASE / 'orch_r139_F4_timer_source_v1/gpu/orch_r139_grid_timer_custody.py'
F4_ROOT = BASE / 'orch_r115_grid_pair_20260915/F4'
TIMER_ROOT = F4_ROOT / 'r140_timer_custody_v1'
F4_CHECKPOINT = BASE / 'orch_r116_shared_node5_20260915_attempt1/generation_000000/sleep/checkpoint/CHECKPOINT.json'
TARGETS = {
    0: dict(label='F1', root=BASE / 'orch_r111_f1_v4_20260915_node5_0_attempt1',
        pid=2664733, start_ticks='6398743', ppid=2664732,
        cmdline_sha256='5b7590a41ba36c1a00f930a81871265fd526d1ec4787a4cfbd0a5dd1fd124efc',
        uuid='GPU-f237c5b5-c2a3-b377-92ee-46cf2658db9a',
        plan_sha256='9a5537780508ac451125d9bc4afde85a45a021fb762498efdf05c070513b884e'),
    3: dict(label='F4', root=F4_ROOT, pid=4148447, start_ticks='7411484', ppid=4148446,
        cmdline_sha256='2c1debfc9db7c15794b33d2cc5b504127904270ac18133831d36016f68798766',
        uuid='GPU-d23c9369-39cf-51fd-833e-13292f173006',
        plan_sha256='afd47a446543700ec1e838fd2584ba05080c9f537a5a70b0ee9483ec3b5cb41c'),
    4: dict(label='A1', root=BASE / 'orch_r111_f1_v4_20260915_node5_4_attempt1',
        pid=3356568, start_ticks='3136146', ppid=3356567,
        cmdline_sha256='683b67c651a9be289bc289eecf959c140e8bc2ca55bb57f09c606e8dbe44d862',
        uuid='GPU-94c9a79c-8b13-5679-ad35-8dda3fe5c94d',
        plan_sha256='14533604ee37024e9ed60c641d39d04eb5cf2156412e3b7409dbcf353031e7ec'),
}


class Blocked(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Blocked(code)


def target(physical):
    require(type(physical) is int and physical in PHYSICALS, 'only_old_0_F1_3_F4_4_A1')
    return TARGETS[physical]


def stamp(path):
    value = Path(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def sha(path):
    before = stamp(path)
    result = route.sha(path)
    require(stamp(path) == before, 'file_changed_during_hash')
    return result


def reference(path):
    return dict(path=str(Path(path).resolve(strict=True)), sha256=sha(path))


def read(path):
    path = Path(path)
    require(path.is_file() and path.stat().st_size <= 32 * 1024 * 1024, 'bounded_metadata_required')
    before = stamp(path)
    def unique(pairs):
        document = {}
        for key, value in pairs:
            require(key not in document, 'duplicate_metadata_key')
            document[key] = value
        return document
    document = json.loads(path.read_bytes(), object_pairs_hook=unique,
        parse_constant=lambda value: require(False, 'nonfinite_metadata'))
    require(stamp(path) == before, 'metadata_changed_during_read')
    return document


def checked_file(value):
    require(isinstance(value, dict) and set(value) == {'path', 'sha256'}, 'exact_file_reference_required')
    path = Path(value['path'])
    require(path.is_absolute() and path.resolve(strict=True) == path and path.is_file(), 'canonical_file_required')
    require(sha(path) == value['sha256'], 'bound_file_changed')
    return path


def checked(value):
    path = checked_file(value)
    document = read(path)
    require(sha(path) == value['sha256'], 'metadata_changed_during_read')
    return document


def bound_stamp(value):
    before = stamp(value['path'])
    checked_file(value)
    require(stamp(value['path']) == before, 'bound_file_changed_during_validation')
    return before


def write(path, document):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        json.dump(document, stream, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def expected_actor(physical):
    lane = target(physical)
    return dict({key: lane[key] for key in ('pid', 'start_ticks', 'ppid', 'cmdline_sha256')},
        uid=2524, boot_id=BOOT)


def identity(pid):
    proc = Path('/proc') / str(pid)
    fields = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'actor_not_live')
    return dict(pid=pid, start_ticks=fields[19], ppid=int(fields[1]), uid=proc.stat().st_uid,
        boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        cmdline_sha256=route.sha(proc / 'cmdline'))


def task_states(pid):
    tasks = list((Path('/proc') / str(pid) / 'task').iterdir())
    require(bool(tasks), 'missing_actor_tasks')
    states = []
    for task in tasks:
        require(not (task / 'children').read_text().strip(), 'readout_or_other_child_in_flight')
        states.append((task / 'stat').read_text().rsplit(')', 1)[1].split()[0])
    return states


def actor_check(physical, *, stopped=False):
    expected = expected_actor(physical)
    require(identity(expected['pid']) == expected, 'exact_actor_identity_changed')
    states = task_states(expected['pid'])
    require(all(state == 'T' for state in states) if stopped else
        all(state not in ('T', 't', 'Z', 'X') for state in states), 'actor_stop_state_not_owned')
    return expected


def host_check():
    require(socket.gethostname() == HOST and os.getuid() == 2524, 'node5_owner_only')
    require(Path('/proc/sys/kernel/random/boot_id').read_text().strip() == BOOT, 'node5_boot_changed')
    require(hasattr(os, 'pidfd_open') and hasattr(signal, 'pidfd_send_signal'), 'pidfd_required')


def gpu_check(physical, *, released=False):
    lane = target(physical)
    def query(arguments):
        result = subprocess.run(['nvidia-smi', *arguments, '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5, check=True)
        return [line.strip().split(', ') for line in result.stdout.splitlines() if line.strip()]
    devices = query(['--query-gpu=index,uuid'])
    require([uuid for index, uuid in devices if int(index) == physical] == [lane['uuid']], 'GPU_mapping_changed')
    owners = query(['--query-compute-apps=gpu_uuid,pid'])
    actual = {int(pid) for uuid, pid in owners if uuid == lane['uuid']}
    require(actual == (set() if released else {lane['pid']}), 'GPU_owner_not_exclusive_or_not_released')


def plan_path(physical):
    lane = target(physical)
    return lane['root'] / ('independent_r119_v1/LEASE_BUDGET.json' if physical == 3 else route.PLAN)


def required_pins(physical):
    lane = target(physical)
    pins = {str(plan_path(physical)): lane['plan_sha256']}
    if physical == 3:
        pins.update({str(F4_SOURCE): 'e6ac3af556de61dbd02278e6510814f6ea1b90cdd4e6fa004aa8faa4fc76aead',
            str(TIMER_SOURCE): grid.TIMER_SHA,
            str(F4_CHECKPOINT): '43ce68acabb18f661ff929600239eb0a632981da841dd1182f886a85df78a02d'})
    else:
        pins[str(ROUTE_SOURCE)] = route.RUN_SHA
        if physical == 0:
            pins[str(F1_STAGE / 'handoff.py')] = '77894fad3b736a05536e26119dee946674bd3c688d1b4db82b448a43a80b9057'
            pins[str(F1_STAGE.parent / 'orch_r139_F1_astra_handoff_20260916_attempt2/handoff.py')] = (
                '22b251d95498fa946d79aed690284c20fc5a2b9f70bb1f2597dde70944ab7fba')
            pins[str(F1_STAGE / 'RESUME_PLAN.json')] = '83c4e949a24ac6e1e6c7096fd8e1a750a354a340e8e11b4025d50977da739843'
            pins[str(F1_STAGE / 'HISTORY.json')] = '9a713943debb8e9bb03bc125652490cdd33ad42c75c39295e8a8baeaddd24fe4'
    return pins


def finite(value):
    return type(value) in (float, int) and math.isfinite(value)


def remaining(request, permission):
    now = time.time()
    require(permission['not_before_unix'] <= now < permission['expires_unix'] <= HARD_END, 'GO_expired_or_future')
    require(now + request['pause_seconds'] + request['exit_seconds'] < min(HARD_END, permission['expires_unix']),
        'donor_retirement_window_exhausted')
    if '_replacement_deadline' in request:
        require(now < request['_replacement_deadline'], 'replacement_readiness_stale')
        require(now + request['remaining_seconds'] + request['exit_seconds'] < request['_replacement_wall'],
            'replacement_window_exhausted')
    for path in request.get('_absent_outputs', []):
        require(not os.path.lexists(path), 'fresh_phase_output_already_exists')


def replacement_budget(replacement, references):
    budget = checked(replacement['lease_budget'])
    prior_ref = budget['derived_from']
    require(prior_ref['sha256'] == GENERIC_LEASE_SHA256, 'actual_generic_R131_lease_bytes_required')
    prior = checked(prior_ref)
    require(prior.get('schema') == 'R131_EXISTING_LEASE_RUNTIME_BUDGET_V1'
        and prior.get('lease_extended') is False and prior.get('safety_margin_seconds') == 600
        and prior.get('hard_end_unix') == COHORT_HARD_END and prior.get('lease_end_unix') == LEASE_END,
        'unchanged_generic_R131_lease_and_wall')
    require(budget.get('schema') == 'R151_EXISTING_NODE5_COHORT_BUDGET_V1'
        and budget.get('physical_devices') == list(PHYSICALS)
        and all(type(value) is int for value in budget['physical_devices'])
        and budget.get('host_sha256') == hashlib.sha256(HOST.encode()).hexdigest()
        and budget.get('lease_extended') is False and budget.get('existing_life_wall_changed') is False
        and budget.get('safety_margin_seconds') == 600 and budget.get('lease_end_unix') == prior['lease_end_unix'],
        'new_cohort_budget_not_donor_extension')
    require(finite(budget.get('hard_end_unix')) and finite(replacement.get('hard_end_unix'))
        and time.time() < replacement['hard_end_unix'] <= budget['hard_end_unix'] <= prior['hard_end_unix']
        and budget['hard_end_unix'] <= budget['lease_end_unix'] - 600, 'new_cohort_existing_lease_ceiling')
    references.extend([replacement['lease_budget'], prior_ref])
    return budget


def new_output_path(value):
    path = Path(value)
    require(path.is_absolute() and path.resolve() == path, 'canonical_new_output_path')
    require(all(path != old['root'] and old['root'] not in path.parents and path not in old['root'].parents
        for old in TARGETS.values()), 'replacement_never_reuses_old_life_root')
    return path


def validate_replacement(request, references, permission):
    replacement = checked(request['replacement'])
    phase, physical = request['replacement_phase'], request['physical']
    require(replacement.get('schema') == 'R151_SELECTED_DONOR_READY_V2'
        and replacement.get('status') == 'READY_FOR_SELECTED_PHASE'
        and replacement.get('phase') == phase and replacement.get('selected_physical') == physical
        and type(replacement.get('selected_physical')) is int
        and replacement.get('new_matched_life') is True and replacement.get('resume') is False
        and replacement.get('post_exit_fresh_admission_required') is True
        and replacement.get('old_artifacts_untouched') is True and replacement.get('blockers') == []
        and replacement.get('physicals') == list(PHYSICALS)
        and all(type(value) is int for value in replacement['physicals']), 'selected_phase_code_readiness_required')
    require(finite(replacement.get('observed_unix')) and 0 <= time.time() - replacement['observed_unix'] <= 120,
        'replacement_readiness_stale')
    budget = replacement_budget(replacement, references)
    request['_replacement_deadline'] = replacement['observed_unix'] + 120
    request['_replacement_wall'] = replacement['hard_end_unix']
    cohort_ref = replacement['cohort']
    cohort = checked(cohort_ref)
    require(cohort.get('schema') == 'R150_MATCHED_CONTINUAL_COHORT_V1'
        and cohort.get('initial_optimizer_steps') == 0 and cohort.get('fresh_histories') is True
        and cohort.get('evaluations_gate_continuation') is False
        and set(cohort['members']) == set(ARM_PHYSICALS)
        and set(replacement['plans']) == set(ARM_PHYSICALS), 'all_three_fresh_cohort_plans_required')
    roots, plans = [], {}
    initial = new_output_path(cohort['initial_directory'])
    for arm, slot in ARM_PHYSICALS.items():
        plan_ref = replacement['plans'][arm]
        plan = checked(plan_ref)
        root = new_output_path(plan['root'])
        require(plan.get('matched_cohort') == cohort_ref and plan.get('matched_arm') == arm
            and type(plan.get('physical')) is int and plan['physical'] == slot
            and plan.get('gpu_uuid') == TARGETS[slot]['uuid']
            and plan.get('parent_enabled') is (arm != 'unparented_learning')
            and plan.get('initialization_validation_schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1'
            and plan.get('authorized_wall_extension') is None and plan.get('preupdate_recovery') is None,
            'new_arm_plan_not_old_life_continuation')
        require(cohort['members'][arm] == dict(root=str(root), gpu_uuid=plan['gpu_uuid'], physical=slot,
            parent_enabled=plan['parent_enabled']) and all(plan.get(key) == value for key, value in cohort['common'].items()),
            'cohort_member_and_common_configuration_join')
        require(plan.get('hard_end_unix') == replacement['hard_end_unix']
            and plan.get('lease_end_unix') == budget['lease_end_unix'], 'plan_uses_new_cohort_not_donor_wall')
        roots.append(root)
        plans[arm] = plan
        references.append(plan_ref)
    require(len(set(roots)) == 3 and not any(first == second or first in second.parents or second in first.parents
        for index, first in enumerate([initial, *roots]) for second in [initial, *roots][index + 1:]),
        'distinct_initial_and_branch_outputs')
    selected_arm = next(arm for arm, slot in ARM_PHYSICALS.items() if slot == physical)
    selected = plans[selected_arm]
    source = Path(selected['source_root'])
    require(source.is_absolute() and source.resolve() == source and source.is_dir()
        and all(source != output and source not in output.parents and output not in source.parents
            for output in [initial, *roots]), 'staged_source_outside_new_outputs')
    manifest = checked(replacement['source_manifest'])
    require(bool(manifest.get('files')), 'staged_replacement_sources_required')
    for relative, digest in manifest['files'].items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'replacement_source_manifest_relative_paths')
        value = dict(path=str(source / relative), sha256=digest)
        checked_file(value)
        references.append(value)
    tests = checked(replacement['tests'])
    require(tests.get('status') == 'PASS'
        and tests.get('source_manifest_sha256') == replacement['source_manifest']['sha256']
        and tests.get('matched_cohort_sha256') == cohort_ref['sha256'], 'replacement_tests_source_cohort_join')
    config = checked(replacement['config'])
    require(config.get('phase') == phase and config.get('matched_arm') == selected_arm
        and config.get('resume') is False and config.get('matched_cohort_sha256') == cohort_ref['sha256']
        and config.get('hard_end_unix') == selected['hard_end_unix']
        and config.get('host_sha256') == hashlib.sha256(HOST.encode()).hexdigest()
        and config.get('boot_id') == BOOT, 'selected_phase_config_binding')
    attempt = new_output_path(config['attempt_dir'])
    require(attempt.parent.is_dir() and all(attempt != output and attempt not in output.parents
        and output not in attempt.parents for output in [initial, source, *roots]), 'separate_new_phase_attempt')
    for name, expected in (('plan', replacement['plans'][selected_arm]), ('lease', replacement['lease_budget']),
            ('source_manifest', replacement['source_manifest']), ('cpu_gate', replacement['tests'])):
        require(dict(path=config.get(name + '_path'), sha256=config.get(name + '_sha256')) == expected,
            'selected_config_reference_join')
    require(config.get('source_pins') == {name: digest for name, digest in manifest['files'].items()
        if name.endswith('.py')}, 'selected_config_source_closure')
    for name in ('allocation', 'intake', 'capsule'):
        value = dict(path=config[name + '_path'], sha256=config[name + '_sha256'])
        checked_file(value)
        references.append(value)
    allocation = read(config['allocation_path'])
    require(allocation.get('plan_sha256') == replacement['plans'][selected_arm]['sha256']
        and allocation.get('cpu_tests_passed') is True and allocation.get('builder_entry_pushed') is True
        and allocation.get('gpu_uuid') == selected['gpu_uuid'] and allocation.get('physical') == physical
        and finite(allocation.get('declared_unix')) and allocation['declared_unix'] <= time.time(),
        'selected_allocation_plan_and_CPU_join')
    references.extend([cohort_ref, replacement['source_manifest'], replacement['tests'], replacement['config']])
    if phase == 'initialize':
        require(physical == 0 and selected_arm == 'parented_learning', 'designated_0_initialize_only')
        require(replacement.get('initialization') is None, 'initialize_does_not_adopt_existing_initial_state')
        absent = [initial, *roots]
    else:
        initialized_ref = replacement.get('initialization')
        require(isinstance(initialized_ref, dict) and initialized_ref.get('path') == str(initial / 'INITIALIZED.json'),
            'bound_common_initialization_required')
        initialized = checked(initialized_ref)
        commit_ref = reference(initial / 'COMMIT.json')
        checkpoint = checked(commit_ref)
        require(initialized.get('cohort_sha256') == cohort_ref['sha256']
            and initialized.get('source_plan_sha256') == replacement['plans']['parented_learning']['sha256']
            and initialized.get('checkpoint_commit_sha256') == commit_ref['sha256']
            and type(checkpoint.get('optimizer_steps')) is int and checkpoint['optimizer_steps'] == 0,
            'run_requires_actual_common_initial_checkpoint')
        validation = initialized['initialization_validation']
        require(validation.get('status') == 'PASS' and validation.get('schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1'
            and validation.get('path') == str(initial / 'capacity_validation/RESULT.json'), 'run_requires_initial_capacity_proof')
        proof_ref = {key: validation[key] for key in ('path', 'sha256')}
        proof = checked(proof_ref)
        require(proof.get('status') == 'PASS' and proof.get('schema') == 'R151_MATCHED_INITIAL_CAPACITY_V1'
            and proof.get('state_restored') is True
            and type(proof.get('optimizer_updates')) is int and proof['optimizer_updates'] == 0,
            'run_requires_restored_common_initial_state')
        references.extend([initialized_ref, commit_ref, proof_ref])
        absent = [Path(selected['root'])]
    request['_absent_outputs'] = [str(path) for path in [*absent, attempt]]
    for value in references:
        path = Path(value['path'])
        require(not any(path == root or root in path.parents for root in roots), 'control_artifacts_outside_branch_outputs')
        require(path != attempt and attempt not in path.parents, 'controls_outside_fresh_phase_attempt')
    remaining(request, permission)
    return [initial, source, attempt, *roots]


def validate_bindings(request_ref, go_ref):
    request, permission = checked(request_ref), checked(go_ref)
    physical = request['physical']
    target(physical)
    require(request['schema'] == 'R151_NODE5_RETIRE_REQUEST_V2' and request['actor'] == expected_actor(physical)
        and request.get('replacement_phase') in ('initialize', 'run'),
        'exact_request_scope')
    require(permission.get('authorized') is True and permission.get('published_by') == 'Main'
        and permission.get('action') == 'retire_old_episodic_actor'
        and permission.get('request') == request_ref and permission.get('replacement') == request['replacement']
        and permission.get('replacement_phase') == request['replacement_phase']
        and permission.get('physical') == physical and type(permission.get('physical')) is int
        and permission.get('actor') == request['actor'] and permission.get('launch_authorized') is False,
        'Main_later_exact_GO_required')
    for key, maximum in (('wait_seconds', 120), ('pause_seconds', 30), ('exit_seconds', 10), ('remaining_seconds', 86400)):
        require(finite(request.get(key)) and 0 < request[key] <= maximum, 'bounded_request_times_required')
    require(all(finite(permission.get(key)) for key in ('not_before_unix', 'expires_unix')), 'bounded_GO_times_required')
    remaining(request, permission)
    pins = request['source_pins']
    require(all(pins.get(path) == digest for path, digest in required_pins(physical).items()), 'old_source_pins_required')
    for source in (__file__, route.__file__, grid.__file__):
        require(pins.get(str(Path(source).resolve())) == sha(source), 'operator_and_helpers_must_be_bound')
    references = [request_ref, go_ref, request['cpu_tests'], request['replacement']]
    for path, digest in pins.items():
        value = dict(path=path, sha256=digest)
        checked_file(value)
        references.append(value)
    cpu = checked(request['cpu_tests'])
    require(cpu.get('passed') is True and cpu.get('source_pins') == pins, 'operator_CPU_gate_must_bind_exact_sources')
    checked_file(cpu['suite'])
    references.append(cpu['suite'])
    roots = validate_replacement(request, references, permission)
    remaining(request, permission)
    stage = Path(request['stage'])
    require(stage.is_absolute() and stage.resolve() == stage and BASE in stage.parents,
        'new_node_local_stage_required')
    require(all(stage != old['root'] and old['root'] not in stage.parents and stage not in old['root'].parents
        for old in TARGETS.values()) and all(stage != root and root not in stage.parents
        and stage not in root.parents for root in roots), 'stage_outside_all_lives')
    require(not stage.exists(), 'one_attempt_stage_already_exists')
    return request, permission, {value['path']: bound_stamp(value) for value in references}


def check_stamps(values):
    require(all(stamp(path) == tuple(expected) for path, expected in values.items()), 'prepared_evidence_changed')


def readout_metadata(root, sleeps, checkpoint):
    guards = {}
    for folder in (root / f'readout_{sleeps:04d}', root / 'open_readouts' / f'readout_{sleeps:04d}'):
        result_path, complete_path = folder / 'PROCESS_RESULT.json', folder / 'COMPLETE.json'
        require(result_path.is_file() and complete_path.is_file(), 'readout_not_complete')
        guards.update({str(path): stamp(path) for path in (result_path, complete_path, folder / 'LAUNCH.json')})
        result = read(result_path)
        require(result.get('status') == 'COMPLETE' and type(result.get('returncode')) is int
            and result['returncode'] == 0 and finite(result.get('finished_unix')), 'readout_failed_or_in_flight')
        launch = read(folder / 'LAUNCH.json')
        require(launch.get('checkpoint') == str(checkpoint) and launch.get('parent_free') is True
            and launch.get('context_free') is True, 'readout_checkpoint_join')
        require(type(launch.get('pid')) is int and not Path('/proc', str(launch['pid'])).exists(),
            'readout_pid_not_reaped_or_reused')
    check_stamps(guards)
    return guards


def route_boundary(root):
    sleeps = sorted(root.glob('cycle_*/SLEEP.json'))
    require(bool(sleeps), 'no_saved_sleep')
    folder = sleeps[-1].parent
    cycle = int(folder.name.split('_')[1])
    guards = {str(sleeps[-1]): stamp(sleeps[-1])}
    saved = read(sleeps[-1])
    require((folder / 'COMPLETE.json').is_file(), 'cycle_not_complete')
    guards[str(folder / 'COMPLETE.json')] = stamp(folder / 'COMPLETE.json')
    complete = read(folder / 'COMPLETE.json')
    require(complete['cycle'] == cycle and complete['sleeps'] == saved['sleeps'], 'completed_sleep_join')
    checkpoint = folder / 'checkpoint/CHECKPOINT.json'
    guards.update(readout_metadata(root, saved['sleeps'], checkpoint))
    ledger = root / 'RESERVATIONS.jsonl'
    before = stamp(ledger)
    rows = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
    require(route.no_future_charges(rows, cycle, saved['sleeps']), 'new_charge_or_readout_in_flight')
    require(stamp(ledger) == before, 'ledger_changed_during_observation')
    guards[str(ledger)] = before
    markers = [root / 'OWN_CARRY.json', checkpoint]
    tracking = root / 'R121_PARENT_DELIVERY'
    if tracking.exists():
        markers.append(tracking)
    guards.update({str(path): stamp(path) for path in markers})
    check_stamps(guards)
    return dict(cycle=cycle, sleeps=saved['sleeps'], ledger=str(ledger),
        guards=guards)


def f4_boundary(root):
    ledger = root / 'LEDGER.jsonl'
    before = stamp(ledger)
    boundary = grid.completed_boundary(root, None)
    require(stamp(ledger) == before, 'F4_new_charge_during_boundary')
    failed = root / 'calls/N04456.json'
    require(sha(failed) == grid.FAILED_SHA, 'F4_historical_failed_charge_changed')
    disposition = read(root / 'r140_continuation_v1/FAILED_PREDISPATCH.json')
    require(disposition.get('failed_call') == reference(failed)
        and disposition.get('status') == 'FAILED_PREDISPATCH_CONTEXT_OVERFLOW', 'F4_failed_charge_disposition_missing')
    require(sha(F4_CHECKPOINT) == required_pins(3)[str(F4_CHECKPOINT)], 'F4_latest_available_checkpoint_changed')
    checkpoint = read(F4_CHECKPOINT)
    for name, digest in checkpoint['adapter']['files']:
        require(Path(name).name == name and sha(Path(checkpoint['adapter']['path']) / name) == digest,
            'F4_saved_adapter_changed')
    return dict(cycle=boundary['cycle'], ledger=str(ledger), checkpoint=reference(F4_CHECKPOINT),
        carry=boundary['carry'], train_complete=boundary['train_complete'],
        retired_predispatch_charges=[4456], exact_continuation_possible=False, sampling_rng_captured=False)


def timer_metadata():
    receipt = TIMER_ROOT / 'ARMED.json'
    require(sha(receipt) == 'ed0f829bed442690da72f24d6400e40ea397a73d1b71752d46f194c016f04dce',
        'F4_timer_receipt_changed')
    controller = read(receipt)['controller_identity']
    require(controller['pid'] == 2957571 and controller['start_ticks'] == '6617958'
        and controller['uid'] == 2524 and controller['boot_id'] == BOOT
        and controller['command_sha256'] == '264dbf1bd756253ec1b3efdc63616311e18ff8c8172660233b40ce038091ccd2',
        'F4_timer_identity_binding_changed')
    try:
        live = identity(controller['pid'])
        alive = (live['start_ticks'] == controller['start_ticks'] and live['boot_id'] == controller['boot_id']
            and live['uid'] == controller['uid'] and live['cmdline_sha256'] == controller['command_sha256'])
    except (FileNotFoundError, ProcessLookupError):
        alive = False
    return dict(controller_pid=controller['pid'], exact_controller_present=alive,
        morning_launch_present=(TIMER_ROOT / 'MORNING_LAUNCH.json').is_file(),
        life_terminal_present=(TIMER_ROOT / 'LIFE_TERMINAL.json').is_file(),
        wall_disposition_present=(TIMER_ROOT / 'WALL_DISPOSITION.json').is_file(),
        blocker='F4_timer_and_phase_process_custody_not_proven')


def inventory(root):
    return {str(path): dict(mode=path.lstat().st_mode, size=path.lstat().st_size,
        symlink=os.readlink(path) if path.is_symlink() else None)
        for path in root.rglob('*')}


def preserved_inventory(before):
    for path, prior in before.items():
        current = Path(path).lstat()
        require(stat.S_IFMT(current.st_mode) == stat.S_IFMT(prior['mode']), 'historical_artifact_type_changed')
        if stat.S_ISREG(prior['mode']):
            require(current.st_size >= prior['size'], 'historical_artifact_truncated')
        if stat.S_ISLNK(prior['mode']):
            require(os.readlink(path) == prior['symlink'], 'historical_artifact_link_changed')


def prepare_boundary(physical):
    lane = target(physical)
    require(physical != 3, 'F4_timer_and_phase_process_custody_not_proven')
    candidate = route_boundary(lane['root'])
    original = read(plan_path(physical))
    document = route.snapshot(lane['root'], original, candidate['cycle'])
    files = dict(document['preserved'])
    files[original['history']['path']] = original['history']['sha256']
    for name, digest in document['adapter']['files']:
        files[str(Path(document['adapter']['path']) / name)] = digest
    guards = dict(candidate['guards'])
    for path, digest in files.items():
        guards[path] = bound_stamp(dict(path=path, sha256=digest))
    archive = inventory(lane['root'])
    check_stamps(candidate['guards'])
    return dict(candidate, preserved_stamps=guards, snapshot=document, inventory=archive)


@contextmanager
def ledger_lock(candidate):
    descriptor = os.open(candidate['ledger'], os.O_RDONLY | os.O_NOFOLLOW)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        actual = os.fstat(descriptor)
        require((actual.st_dev, actual.st_ino) == tuple(candidate['guards'][candidate['ledger']][:2]),
            'ledger_inode_replaced')
        yield
    finally:
        os.close(descriptor)


def send(descriptor, physical, signum):
    require(signum in (signal.SIGSTOP, signal.SIGTERM, signal.SIGCONT), 'narrow_stop_only_no_force_kill')
    actual, expected = identity(target(physical)['pid']), expected_actor(physical)
    if signum == signal.SIGCONT:
        actual.pop('ppid')
        expected.pop('ppid')
    require(actual == expected, 'identity_before_pidfd_signal')
    signal.pidfd_send_signal(descriptor, signum)


def release_candidate(physical, candidate, request, permission, binding_stamps, stage):
    actor_check(physical)
    check_stamps(binding_stamps)
    descriptor = os.pidfd_open(target(physical)['pid'])
    paused, term_sent = False, False
    signal_guard = threading.Lock()
    watchdog = None
    timed_out = threading.Event()
    restore_errors = []
    pause_deadline = time.monotonic() + min(request['pause_seconds'], permission['expires_unix'] - time.time(),
        request.get('_replacement_deadline', permission['expires_unix']) - time.time())
    def restore_on_timeout():
        nonlocal paused
        with signal_guard:
            timed_out.set()
            if paused:
                try:
                    send(descriptor, physical, signal.SIGCONT)
                    paused = False
                except Exception as error:
                    restore_errors.append(type(error).__name__)
    try:
        actor_check(physical)
        with ledger_lock(candidate):
            remaining(request, permission)
            check_stamps(candidate['guards'])
            actor_check(physical)
            send(descriptor, physical, signal.SIGSTOP)
            paused = True
            stop_deadline = min(pause_deadline, time.monotonic() + .25)
            while not all(state == 'T' for state in task_states(target(physical)['pid'])):
                require(time.monotonic() < stop_deadline, 'bounded_stop_not_observed')
                time.sleep(.005)
            actor_check(physical, stopped=True)
            check_stamps(candidate['guards'])
        watchdog = threading.Timer(max(0, pause_deadline - time.monotonic()), restore_on_timeout)
        watchdog.start()
        saved = prepare_boundary(physical)
        check_stamps(candidate['guards'])
        require(saved['cycle'] == candidate['cycle'], 'saved_cycle_changed_after_pause')
        candidate = saved
        require(time.monotonic() < pause_deadline, 'pause_budget_expired')
        write(stage / 'BOUNDARY.json', candidate)
        check_stamps(candidate['preserved_stamps'])
        check_stamps(binding_stamps)
        with ledger_lock(candidate):
            with signal_guard:
                remaining(request, permission)
                require(not timed_out.is_set() and time.monotonic() < pause_deadline, 'pause_budget_expired')
                actor_check(physical, stopped=True)
                check_stamps(candidate['guards'])
                send(descriptor, physical, signal.SIGTERM)
                term_sent = True
                send(descriptor, physical, signal.SIGCONT)
                paused = False
        require(bool(select.select([descriptor], [], [], request['exit_seconds'])[0]), 'TERM_sent_exit_unconfirmed')
        require(sha(candidate['ledger']) == candidate['snapshot']['preserved'][candidate['ledger']],
            'charge_during_retirement')
        check_stamps(candidate['preserved_stamps'])
        preserved_inventory(candidate['inventory'])
        gpu_check(physical, released=True)
        write(stage / 'RELEASED.json', dict(status='RELEASED_OLD_EPISODIC_ACTOR', physical=physical,
            actor=expected_actor(physical), boundary=reference(stage / 'BOUNDARY.json'),
            replacement=request['replacement'], replacement_phase=request['replacement_phase'],
            released_unix=time.time(), launch_authorized=False,
            new_life_not_continuation=True, post_exit_privileged_admission_required=True,
            parents_untouched=True, existing_artifacts_preserved=True, no_force_kill=True))
        return dict(status='RELEASED_OLD_EPISODIC_ACTOR', physical=physical, release=reference(stage / 'RELEASED.json'),
            replacement_phase=request['replacement_phase'], launch_authorized=False, post_exit_privileged_admission_required=True)
    except BaseException:
        write(stage / 'SIGNAL_DISPOSITION.json', dict(term_sent=term_sent, exit_verified=False,
            retry_authorized=False, no_force_kill=True, watchdog_expired=timed_out.is_set(),
            watchdog_restore_errors=restore_errors))
        raise
    finally:
        try:
            if watchdog is not None:
                watchdog.cancel()
                watchdog.join()
            if paused:
                send(descriptor, physical, signal.SIGCONT)
        finally:
            os.close(descriptor)


def retire(request_ref, go_ref):
    request, permission, bindings = validate_bindings(request_ref, go_ref)
    host_check()
    physical = request['physical']
    require(identity(target(physical)['pid']) == expected_actor(physical), 'exact_actor_identity_changed')
    if physical == 3:
        timer_metadata()
        raise Blocked('F4_timer_and_phase_process_custody_not_proven')
    stage = Path(request['stage'])
    stage.mkdir(mode=0o700)
    try:
        snapshots = stage / 'sources'
        snapshots.mkdir(mode=0o700)
        for path, digest in request['source_pins'].items():
            destination = snapshots / digest
            if not destination.exists():
                with destination.open('xb') as stream:
                    stream.write(Path(path).read_bytes())
            require(sha(destination) == digest, 'source_snapshot_changed')
        check_stamps(bindings)
        remaining(request, permission)
        write(stage / 'ARMED.json', dict(request=request_ref, main_go=go_ref,
            replacement=request['replacement'], replacement_phase=request['replacement_phase'],
            armed_unix=time.time(), source_snapshots=True,
            protected_physicals=list(PROTECTED), signals_sent=0, launch_authorized=False))
        deadline = min(time.monotonic() + request['wait_seconds'],
            time.monotonic() + permission['expires_unix'] - time.time())
        candidate = None
        while time.monotonic() < deadline:
            remaining(request, permission)
            try:
                actor_check(physical)
                gpu_check(physical)
                candidate = route_boundary(target(physical)['root'])
                break
            except (Blocked, FileNotFoundError, ValueError, KeyError):
                time.sleep(.05)
        require(candidate is not None and time.monotonic() < deadline, 'no_saved_boundary_within_wait_budget')
        return release_candidate(physical, candidate, request, permission, bindings, stage)
    except BaseException as error:
        write(stage / 'BLOCKED.json', dict(status='BLOCKED', reason=str(error) if isinstance(error, Blocked)
            else 'evidence_or_runtime_validation_failed', error_type=type(error).__name__,
            retry_authorized=False, launch_authorized=False, observed_unix=time.time()))
        raise


def inspect_lane(physical):
    lane = target(physical)
    result = dict(status='READ_ONLY_NOT_ARMED', physical=physical, label=lane['label'],
        protected_physicals=list(PROTECTED), signals_sent=0, remote_mutations=0,
        launch_authorized=False, blockers=[], observed_unix=time.time())
    for name, check in [('host', host_check), ('actor', lambda: actor_check(physical)),
            ('GPU', lambda: gpu_check(physical))]:
        try:
            check()
        except Exception:
            result['blockers'].append(name + '_not_verified')
    try:
        if physical == 3:
            result['boundary'] = f4_boundary(lane['root'])
        else:
            boundary = route_boundary(lane['root'])
            result['boundary'] = {key: boundary[key] for key in ('cycle', 'sleeps')}
    except Exception:
        result['blockers'].append('saved_boundary_not_verified')
    if physical == 3:
        result['availability_limitation'] = F4_LIMITATION
        try:
            result['timer'] = timer_metadata()
        except Exception:
            result['blockers'].append('F4_timer_metadata_not_verified')
        result['blockers'].append('F4_timer_and_phase_process_custody_not_proven')
    result['blockers'].append('Main_later_exact_GO_and_bound_ready_replacement_required')
    return result


def contract(physical):
    target(physical)
    return dict(schema='R151_NODE5_RETIRE_REQUEST_V2', physical=physical,
        replacement_phase='initialize' if physical == 0 else 'run',
        actor=expected_actor(physical), stage=None, source_pins=required_pins(physical),
        cpu_tests=None, replacement=None, wait_seconds=30, pause_seconds=10,
        exit_seconds=5, remaining_seconds=None, Main_later_exact_GO_required=True,
        operator_and_helper_source_pins_required=True, protected_physicals=list(PROTECTED),
        donor_retirement_hard_end_unix=HARD_END, new_cohort_ceiling_unix=COHORT_HARD_END,
        new_cohort_generic_lease_sha256=GENERIC_LEASE_SHA256,
        F4_availability_limitation=F4_LIMITATION, launch_authorized=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('contract', 'inspect', 'retire'))
    parser.add_argument('--physical', type=int, choices=PHYSICALS)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--request-sha256')
    parser.add_argument('--go', type=Path)
    parser.add_argument('--go-sha256')
    args = parser.parse_args()
    if args.mode != 'retire':
        require(args.physical is not None, 'physical_required')
        result = contract(args.physical) if args.mode == 'contract' else inspect_lane(args.physical)
    else:
        require(args.physical is None, 'retire_scope_comes_only_from_bound_request')
        require(all((args.request, args.request_sha256, args.go, args.go_sha256)), 'exact_request_and_GO_bytes_required')
        result = retire(dict(path=str(args.request), sha256=args.request_sha256),
            dict(path=str(args.go), sha256=args.go_sha256))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(json.dumps(dict(status='BLOCKED', reason=str(error) if isinstance(error, Blocked)
            else 'evidence_or_runtime_validation_failed', error_type=type(error).__name__, launch_authorized=False)))
        raise SystemExit(2)
