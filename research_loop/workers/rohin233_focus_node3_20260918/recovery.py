"""Explicit human-authorized recovery of eight exited node3 lives, never old roots."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from retirement import PROTECTED, census, is_native, metadata, record, save, sha
from recovery_runtime import entrypoint


PHASE = 'r233_recovery_20260918'


def utc(value=None):
    return datetime.fromtimestamp(time.time() if value is None else value, timezone.utc).isoformat()


def read(path):
    return json.loads(path.read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checked_deadline(plan, guard, observed, budget=43200):
    require(0 < budget <= 43200, 'explicit_at_most_twelve_hour_budget')
    deadline = min(observed + budget, plan['lease_end_unix'] - 21600, guard['next_reserved_unix'] - 120)
    require(deadline - observed >= 3600, 'sufficient_existing_lease_and_reservation_budget')
    return deadline


def relocated_plan(previous, source, deadline):
    plan = deepcopy(previous)
    old_source = Path(previous['source_root'])
    plan.update(source_root=str(source), hard_end_unix=deadline)
    require('authorized_wall_extension' not in plan and 'preupdate_recovery' not in plan,
        'do_not_layer_unexamined_recovery_protocols')
    if 'startup_context' in plan:
        plan['startup_context']['path'] = str(source / Path(plan['startup_context']['path']).relative_to(old_source))
    entrypoint(plan)
    return plan


def offline_inbox(plan):
    return Path(plan['root']) / 'stream/inbox'


def inactive(root, name):
    require(name in PROTECTED, 'exact_kept_life_allowlist')
    require(not any(name in item['lives'] and is_native(item) for item in census(root)),
        'never_restart_live_kept_native')


def context(root, name):
    inactive(root, name)
    arm = root / name
    active = read(arm / 'ACTIVE_RUNTIME.json')
    old = Path(active['control'])
    plan, guard = read(old / 'PLAN.json'), read(old / 'GUARD.json')
    require(plan['physical'] == PROTECTED[name] and sha(old / 'PLAN.json') == guard['plan_sha256'],
        'exact_existing_plan_and_original_device')
    require(sha(Path(guard['lease_path'])) == guard['lease_sha256'], 'original_lease_receipt_binding')
    lease = read(Path(guard['lease_path']))
    require(lease['lease_end_unix'] == plan['lease_end_unix'], 'unchanged_verified_physical_lease')
    exited = read(old / 'EXIT.json')
    require(exited['exit_code'] == 124 and 5 <= plan['hard_end_unix'] - exited['finished_unix'] <= 20,
        'actual_guard_timeout_requires_this_recovery_not_unknown_failure')
    paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    complete_path = next(path for path in reversed(paths) if metadata(path) == 'SLEEP_COMPLETE')
    complete, head = record(complete_path), record(paths[-1])
    loaded = next(record(path) for path in reversed(paths) if metadata(path) == 'LOADED')
    require(not Path('/proc', str(loaded['document']['pid'])).exists(), 'old_pid_not_reused_or_alive')
    return arm, old, plan, guard, paths, complete_path, complete, head, loaded, exited


def environment(source, root):
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTHONPATH=os.pathsep.join((str(source), str(source / 'gpu'), str(source / 'tests'), str(root))))


def manifest(directory):
    return {str(path.relative_to(directory)): sha(path) for path in sorted(directory.rglob('*')) if path.is_file()}


def audit(root, output):
    rows = []
    for name in PROTECTED:
        arm, old, plan, guard, paths, complete_path, complete, head, loaded, exited = context(root, name)
        tail = [record(path) for path in paths if int(path.stem) > complete['index']]
        rows.append(dict(life=name, gpu=PROTECTED[name], old_pid=loaded['document']['pid'],
            actual_exit=exited, operator_deadline_utc=utc(plan['hard_end_unix']),
            guard_timeout_margin_seconds=plan['hard_end_unix'] - exited['finished_unix'],
            latest_complete=dict(index=complete['index'], sha256=complete['sha256'],
                cycle=complete['document']['cycle'], checkpoint_sha256=complete['document']['checkpoint_sha256']),
            head=dict(index=head['index'], sha256=head['sha256']),
            unsaved_tail_updates=sum(item['kind'] == 'UPDATE' for item in tail),
            tail_responses=sum(item['kind'] == 'RESPONSE' for item in tail),
            logs={filename: sha(old / filename) for filename in ('EXIT.json', 'FAILED.json', 'NATIVE.log', 'supervisor.log')},
            lease_end_utc=utc(plan['lease_end_unix']), max_sleeps=plan['max_sleeps']))
    save(output, dict(observed_utc=utc(), node='node3', cause='configured_operator_timeout_exit124',
        no_automatic_retry=True, new_human_recovery_authorization=True, rows=rows,
        reboot_claimed=False, OOM_claimed=False, native_signals=0))
    print(json.dumps(dict(audited=len(rows), receipt_sha256=sha(output))))


def prepare(root, name, python):
    arm, old, previous, guard, paths, complete_path, complete, head, loaded, exited = context(root, name)
    control, source, preserved = arm / ('control_' + PHASE), arm / ('source_' + PHASE), arm / PHASE
    require(not any(path.exists() for path in (control, source, preserved)), 'one_new_recovery_attempt')
    source_old = Path(previous['source_root'])
    require(manifest_python(source_old) == guard['source_pins'], 'entire_old_source_exact')
    deadline = checked_deadline(previous, guard, time.time())
    preserved.mkdir(mode=0o700)
    control.mkdir(mode=0o700)
    checkpoint_dir = arm / 'raw/checkpoints' / ('sleep_%06d' % complete['document']['cycle'])
    for origin, target in ((arm / 'raw/stream', preserved / 'stream'),
            (checkpoint_dir, preserved / checkpoint_dir.name), (old, preserved / 'failed_control')):
        subprocess.run(['cp', '-a', '--reflink=auto', str(origin), str(target)], check=True)
    save(preserved / 'MANIFEST.json', manifest(preserved))
    shutil.copytree(source_old, source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(Path(__file__).with_name('recovery_runtime.py'), source / 'gpu/r233_recovery_runtime.py')
    recovery_source = root / 'r213_math_a/source_r226_resume/gpu/r213_recovery_runtime.py'
    if not (source / 'gpu/r213_recovery_runtime.py').exists():
        shutil.copy2(recovery_source, source / 'gpu/r213_recovery_runtime.py')
    plan = relocated_plan(previous, source, deadline)
    sys.path[:0] = [str(source), str(source / 'gpu'), str(root)]
    from gpu.r213_recovery_runtime import RecoveryJournal, saved_state
    from gpu.orch_r125_continual_native import NativeChild
    from organism_v6.orch_r125_continual_stream import verify_experiment_resume
    restored = saved_state(complete, deadline)
    verify_experiment_resume(plan, restored['state']['experiment'])
    checkpoint = deepcopy(read(checkpoint_dir / 'COMMIT.json'))
    checkpoint.update(adapter_path=str(checkpoint_dir / 'adapter'), optimizer_rng_path=str(checkpoint_dir / 'optimizer_rng.pt'))
    NativeChild.verify_checkpoint(checkpoint)
    import torch
    payload = torch.load(checkpoint_dir / 'optimizer_rng.pt', map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] and not torch.cuda.is_initialized(),
        'actual_optimizer_RNG_CPU_check_no_GPU')
    tail = [record(path) for path in paths if int(path.stem) > complete['index']]
    receipt = dict(old_native_absent=True, old_native_pid=loaded['document']['pid'],
        old_outer_exit_status=exited['exit_code'], exact_resident_continuity_claimed=False,
        old_head_index=head['index'], old_head_sha256=head['sha256'], complete_path=str(complete_path),
        complete_sha256=complete['sha256'], new_deadline_unix=deadline, complete_cycle=complete['document']['cycle'],
        optimizer_steps=checkpoint['optimizer_steps'], checkpoint_sha256=checkpoint['checkpoint_sha256'],
        preservation_manifest_sha256=sha(preserved / 'MANIFEST.json'), old_plan_sha256=sha(old / 'PLAN.json'),
        lost_tail_updates=sum(item['kind'] == 'UPDATE' for item in tail),
        tail_responses=[dict(index=item['index'], sha256=item['sha256']) for item in tail if item['kind'] == 'RESPONSE'],
        tail_inbox_ids=[item['document']['message']['id'] for item in tail if item['kind'] == 'INBOX'],
        original_tail_records_retained=True, birth_compaction_repeated=False, same_journal=True,
        human_authorization='2026-09-18 explicit recovery of eight kept node3 lives')
    save(control / 'RECOVERY.json', receipt)
    class OfflineJournal(RecoveryJournal):
        def _reload_state(self, *arguments, **keywords):
            self.inbox = offline_inbox(plan)
            return super()._reload_state(*arguments, **keywords)
    replay = control / 'replay_stream'
    subprocess.run(['cp', '-a', '--reflink=auto', str(preserved / 'stream'), str(replay)], check=True)
    with OfflineJournal(replay) as journal:
        proof = journal.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(control / 'RECOVERY.json'),
            receipt_sha256=sha(control / 'RECOVERY.json'), state=restored))
        require(journal.latest_checkpoint()['document'] == restored, 'actual_archive_replay')
    save(control / 'ARCHIVE_REPLAY.json', dict(reference=proof, verified=True, live_journal_unchanged=True))
    from r226_correction_boundary import select_cache
    corrections = [record(path) for path in paths if metadata(path) == 'R197_CORRECTION_CYCLE']
    selected = select_cache(corrections, complete)
    save(control / 'CORRECTION_CACHE_RECOVERY.json', dict(before=read(arm / 'raw/stream/correction_ledger.json'), after=selected))
    save(control / 'PLAN.json', plan)
    lease = read(Path(guard['lease_path']))
    lease.update(hard_end_unix=deadline, actual_physical_lease_changed=False, operator_screen_cap_seconds=43200)
    save(control / 'LEASE.json', lease)
    tests = ['test_r205_runtime', 'test_orch_r184_think_act_learn']
    tests.append('test_r227_caption' if 'caption_' in name else 'test_r226_math_runtime')
    with (control / 'CPU.log').open('x') as log:
        result = subprocess.run([python, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source, root), stdout=log, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_CPU_gate')
    pins = manifest_python(source)
    save(control / 'RECEIVING_CPU.json', dict(passed=True, tests=tests, source_pins=pins,
        log_sha256=sha(control / 'CPU.log'), archive_replay_sha256=sha(control / 'ARCHIVE_REPLAY.json')))
    allocation = read(Path(guard['allocation_path']))
    allocation.update(plan_sha256=sha(control / 'PLAN.json'), cpu_tests_passed=True,
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'),
        declared_unix=time.time())
    save(control / 'ALLOCATION.json', allocation)
    guard.update(source_pins=pins, resume=True, attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=deadline, lease_path=str(control / 'LEASE.json'),
        lease_sha256=sha(control / 'LEASE.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    save(control / 'GUARD.json', guard)
    subprocess.run([python, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source, root), check=True, timeout=40)
    save(control / 'READY.json', dict(passed=True, original_journal_unchanged=True, native_launched=False))
    print(json.dumps(dict(life=name, status='READY_NOT_LAUNCHED', cycle=receipt['complete_cycle'],
        lost_tail_updates=receipt['lost_tail_updates'], deadline_utc=utc(deadline), receipt_sha256=sha(control / 'RECOVERY.json'))))


def manifest_python(source):
    return {str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')}


def current_control(arm):
    default = arm / ('control_' + PHASE)
    active = read(arm / 'ACTIVE_RUNTIME.json')
    selected = Path(active['control'])
    if selected.parent == arm and selected.name in (default.name, default.name + '_admission_retry1',
            default.name + '_policy', default.name + '_policy_lease_ceiling',
            default.name + '_boundary_lease_ceiling'):
        return selected
    return default


def adopt_policy(root, name, python):
    inactive(root, name)
    arm = root / name
    old = arm / ('control_' + PHASE)
    require(read(old / 'READY.json')['passed'] and not (old / 'DISPATCHED.json').exists(), 'stopped_unlaunched_policy_adoption_only')
    source = arm / ('source_' + PHASE + '_policy')
    control = arm / (old.name + '_policy')
    control.mkdir(mode=0o700)
    shutil.copytree(Path(read(old / 'PLAN.json')['source_root']), source,
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    overlay = root / 'r227_policy_overlay'
    pins = read(overlay / 'MANIFEST.json')
    for relative, digest in pins.items():
        require(sha(overlay / relative) == digest, 'exact_already_tested_Main_R227_overlay')
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(overlay / relative, target)
    reference = root / 'r213_r226_caption_observation_fork/source_r227_policy_ready'
    for relative in ('tests/test_orch_r205_reading_policy.py',
            'organism_v6/orch_r225_content_target_filter.py'):
        if not (source / relative).exists():
            shutil.copy2(reference / relative, source / relative)
    sys.path[:0] = [str(root), str(source), str(source / 'gpu')]
    from r227_policy_stage import policy_plan
    from gpu.orch_r125_continual_native import validate_plan
    from gpu.orch_r184_think_act_learn import validate_config
    from organism_v6.orch_r125_continual_stream import verify_experiment_resume
    previous = read(old / 'PLAN.json')
    plan = policy_plan(previous, source)
    validate_plan(plan)
    validate_config(plan['think_act_learn'])
    receipt = read(old / 'RECOVERY.json')
    verify_experiment_resume(plan, record(Path(receipt['complete_path']))['document']['resume_state']['state']['experiment'])
    tests = ['test_orch_r227_learning_policy', 'test_orch_r184_think_act_learn',
        'test_orch_r205_reading_policy', 'test_orch_r194_code_target_filter', 'test_orch_r195_learn_review_filter']
    with (control / 'CPU.log').open('x') as output:
        result = subprocess.run([python, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source, root), stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'R227_actual_receiving_tests_and_provenance')
    end = time.time() + 900
    while not (old / 'RECONCILED.json').exists():
        require(time.time() < end, 'prior_reconciliation_must_finish_without_native_launch')
        time.sleep(5)
    inactive(root, name)
    require(not (old / 'DISPATCHED.json').exists(), 'not_started_during_policy_gate')
    verify_reconciled(arm, old)
    for filename in ('LEASE.json', 'READY.json', 'RECOVERY.json', 'RECONCILED.json',
            'RECOVERY_APPENDED.json', 'ARCHIVE_REPLAY.json', 'CORRECTION_CACHE_RECOVERY.json',
            'TAIL_ARTIFACTS_PRESERVED.json'):
        shutil.copy2(old / filename, control / filename)
    save(control / 'PLAN.json', plan)
    source_pins = manifest_python(source)
    save(control / 'RECEIVING_CPU.json', dict(passed=True, tests=tests, source_pins=source_pins,
        log_sha256=sha(control / 'CPU.log'), overlay=pins, learn_row_policy=plan['learn_row_policy'],
        source_bound_prior_replay_sha256=sha(old / 'ARCHIVE_REPLAY.json'),
        historical_rows_unchanged=True, actual_sleep_recipe_pending=True))
    allocation = read(old / 'ALLOCATION.json')
    allocation.update(declared_unix=time.time(), plan_sha256=sha(control / 'PLAN.json'),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'))
    save(control / 'ALLOCATION.json', allocation)
    guard = read(old / 'GUARD.json')
    guard.update(source_pins=source_pins, attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), lease_path=str(control / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    save(control / 'GUARD.json', guard)
    subprocess.run([python, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source, root), check=True, timeout=40)
    active = arm / 'ACTIVE_RUNTIME.r233.policy.tmp'
    save(active, dict(source=str(source), control=str(control), module='gpu.r233_recovery_runtime',
        recovery_receipt=str(old / 'RECOVERY.json')))
    os.replace(active, arm / 'ACTIVE_RUNTIME.json')
    save(control / 'POLICY_READY.json', dict(policy=plan['learn_row_policy'], native_launched=False,
        same_checkpoint=True, actual_sleep_recipe_pending=True))
    print(json.dumps(dict(life=name, status='POLICY_READY_NOT_LAUNCHED', policy=plan['learn_row_policy'])))


def retry_policy(root, name, python):
    inactive(root, name)
    arm = root / name
    control = arm / ('control_' + PHASE + '_policy')
    source = arm / ('source_' + PHASE + '_policy')
    require(not any((control / filename).exists() for filename in
        ('POLICY_READY.json', 'DISPATCHED.json', 'PLAN.json')), 'only_unlaunched_failed_policy_gate')
    require("No module named 'organism_v6.orch_r225_content_target_filter'" in
        (control / 'CPU.log').read_text(), 'exact_missing_dependency_failure')
    for path in (control, source):
        destination = path.with_name(path.name + '_missing_dependency_preserved')
        require(not destination.exists(), 'failed_source_preservation_destination_unused')
    for path in (control, source):
        path.rename(path.with_name(path.name + '_missing_dependency_preserved'))
    adopt_policy(root, name, python)


def retry_admission(root, name, python):
    inactive(root, name)
    arm = root / name
    old = arm / ('control_' + PHASE)
    source = arm / ('source_' + PHASE)
    require(read(old / 'OUTER_FAILED.json')['error'] == 'fresh_privileged_admission'
        and not (old / 'LAUNCH.json').exists() and not (old / 'NATIVE.log').exists(),
        'only_proven_pre_native_admission_rejection')
    require(not Path('/proc', str(read(old / 'DISPATCHED.json')['pid'])).exists(), 'failed_outer_absent')
    verify_reconciled(arm, old)
    report = json.loads(subprocess.check_output(['sudo', '-n', 'env', 'CUDA_VISIBLE_DEVICES=',
        'PYTHONDONTWRITEBYTECODE=1', 'PYTHONPATH=' + str(source), python, '-B', '-m',
        'gpu.r233_recovery_runtime', 'scan', '--config', str(old / 'GUARD.json')], cwd=source,
        text=True, timeout=100))
    require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons'],
        'fresh_clear_privileged_admission_before_separate_attempt')
    control = arm / (old.name + '_admission_retry1')
    control.mkdir(mode=0o700)
    for filename in ('PLAN.json', 'LEASE.json', 'RECEIVING_CPU.json', 'READY.json', 'RECOVERY.json',
            'RECONCILED.json', 'RECOVERY_APPENDED.json', 'ARCHIVE_REPLAY.json',
            'CORRECTION_CACHE_RECOVERY.json', 'TAIL_ARTIFACTS_PRESERVED.json'):
        shutil.copy2(old / filename, control / filename)
    save(control / 'FRESH_ADMISSION.json', report)
    save(control / 'PREVIOUS_REJECTED_ATTEMPT.json', dict(previous_relative=old.name,
        failed_sha256=sha(old / 'OUTER_FAILED.json'), native_was_not_started=True,
        unknown_original_scan_details_not_invented=True, observed_utc=utc()))
    allocation = read(old / 'ALLOCATION.json')
    allocation.update(declared_unix=time.time(), cpu_receipt_path=str(control / 'RECEIVING_CPU.json'))
    save(control / 'ALLOCATION.json', allocation)
    guard = read(old / 'GUARD.json')
    guard.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        lease_path=str(control / 'LEASE.json'), allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    save(control / 'GUARD.json', guard)
    active = arm / 'ACTIVE_RUNTIME.r233.admission.tmp'
    save(active, dict(source=str(source), control=str(control), module='gpu.r233_recovery_runtime',
        recovery_receipt=str(old / 'RECOVERY.json')))
    os.replace(active, arm / 'ACTIVE_RUNTIME.json')
    print(json.dumps(dict(life=name, status='SEPARATE_ATTEMPT_READY_NOT_LAUNCHED',
        fresh_admission_sha256=sha(control / 'FRESH_ADMISSION.json'))))


def conservative_ceiling(plan, guard, observed):
    ceiling = datetime(2026, 9, 24, 18, tzinfo=timezone.utc).timestamp()
    deadline = min(ceiling, plan['lease_end_unix'] - 21600, guard['next_reserved_unix'] - 21600)
    require(deadline > observed + 3600, 'lease_aware_remaining_budget_not_new_short_experiment')
    return deadline


def derived_budget_lease(previous, deadline, prior_sha256):
    require(deadline <= previous['lease_end_unix'] - 21600, 'unchanged_existing_physical_lease_margin')
    lease = deepcopy(previous)
    lease.update(hard_end_unix=deadline, operator_screen_cap_seconds=None,
        operator_budget_basis='USER_20260918_DATE_ONLY_SEP25_MINUS_SIX_HOURS',
        previous_operator_budget_receipt_sha256=prior_sha256,
        actual_physical_lease_changed=False, new_provider_expiry_claimed=False)
    return lease


def extend_prepared(root, name, python):
    inactive(root, name)
    arm = root / name
    old = current_control(arm)
    previous = read(old / 'PLAN.json')
    require(read(old / 'POLICY_READY.json')['policy'] == 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1',
        'stopped_R227_receiving_gate_required')
    if (old / 'DISPATCHED.json').exists():
        require(read(old / 'OUTER_FAILED.json')['error'] == 'fresh_privileged_admission'
            and not (old / 'LAUNCH.json').exists() and not (old / 'NATIVE.log').exists(),
            'only_pre_native_failed_attempt_may_get_new_authorized_budget')
        require(not Path('/proc', str(read(old / 'DISPATCHED.json')['pid'])).exists(), 'old_outer_absent')
    verify_reconciled(arm, old)
    source = Path(previous['source_root'])
    require(manifest_python(source) == read(old / 'GUARD.json')['source_pins'], 'unchanged_tested_receiving_source')
    plan = deepcopy(previous)
    require(not plan.get('authorized_wall_extension'), 'one_new_supported_wall_extension')
    reference = read(old / 'RECONCILED.json')['recovery_record']
    saved = record(arm / 'raw/stream/records' / f"{reference['index']:020d}.json")['document']['state']
    plan['hard_end_unix'] = conservative_ceiling(plan, read(old / 'GUARD.json'), time.time())
    plan['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=saved['state']['deadline_unix'], previous_stream_sha256=saved['sha256'],
        new_deadline_unix=plan['hard_end_unix'], lease_end_unix=plan['lease_end_unix'], safety_margin_seconds=21600)
    control = arm / (old.name + '_lease_ceiling')
    control.mkdir(mode=0o700)
    for filename in ('READY.json', 'RECOVERY.json', 'RECONCILED.json',
            'RECOVERY_APPENDED.json', 'ARCHIVE_REPLAY.json', 'CORRECTION_CACHE_RECOVERY.json',
            'TAIL_ARTIFACTS_PRESERVED.json', 'POLICY_READY.json'):
        shutil.copy2(old / filename, control / filename)
    save(control / 'LEASE.json', derived_budget_lease(read(old / 'LEASE.json'),
        plan['hard_end_unix'], sha(old / 'LEASE.json')))
    save(control / 'PLAN.json', plan)
    code = ('import json,sys; from pathlib import Path; '
        'from organism_v6.orch_r125_continual_stream import ContinualStream,digest; '
        'from gpu.orch_r125_continual_native import prepare_wall_extension; '
        'plan=json.loads(Path(sys.argv[1]).read_bytes()); '
        'saved=json.loads(Path(sys.argv[2]).read_bytes())["document"]["state"]; '
        'stream=ContinualStream.restore(saved,expected_sha256=saved["sha256"]); '
        'proof=prepare_wall_extension(plan,stream,resume=True,plan_sha256=sys.argv[3]); '
        'assert stream.deadline_unix==saved["state"]["deadline_unix"]; '
        'print(json.dumps(dict(passed=True,proof_sha256=digest(proof),prior_state_unchanged=True)))')
    result = subprocess.run([python, '-B', '-c', code, str(control / 'PLAN.json'),
        str(arm / 'raw/stream/records' / f"{reference['index']:020d}.json"), sha(control / 'PLAN.json')],
        cwd=source, env=environment(source, root), capture_output=True, text=True, timeout=60)
    save(control / 'WALL_CPU.json', dict(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr))
    require(result.returncode == 0, 'existing_R131_saved_boundary_wall_gate')
    cpu = read(old / 'RECEIVING_CPU.json')
    cpu.update(prior_receiving_sha256=sha(old / 'RECEIVING_CPU.json'), wall_cpu_sha256=sha(control / 'WALL_CPU.json'))
    save(control / 'RECEIVING_CPU.json', cpu)
    save(control / 'LEASE_CEILING_AUTHORIZATION.json', dict(observed_utc=utc(),
        user_date_only='2026-09-25', conservative_finish_utc=utc(plan['hard_end_unix']),
        new_provider_expiry_claimed=False, lease_extended=False, native_source_unchanged=True,
        stopped_life_only=True, actual_WALL_EXTENDED_pending=True))
    allocation = read(old / 'ALLOCATION.json')
    allocation.update(declared_unix=time.time(), plan_sha256=sha(control / 'PLAN.json'),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'))
    save(control / 'ALLOCATION.json', allocation)
    guard = read(old / 'GUARD.json')
    guard.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'),
        plan_sha256=sha(control / 'PLAN.json'), hard_end_unix=plan['hard_end_unix'],
        lease_path=str(control / 'LEASE.json'), lease_sha256=sha(control / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'),
        allocation_sha256=sha(control / 'ALLOCATION.json'))
    save(control / 'GUARD.json', guard)
    subprocess.run([python, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source, root), check=True, timeout=40)
    active = arm / 'ACTIVE_RUNTIME.r233.ceiling.tmp'
    save(active, dict(source=str(source), control=str(control), module='gpu.r233_recovery_runtime',
        recovery_receipt=str(control / 'RECOVERY.json')))
    os.replace(active, arm / 'ACTIVE_RUNTIME.json')
    print(json.dumps(dict(life=name, status='LEASE_CEILING_READY_NOT_LAUNCHED', deadline_utc=utc(plan['hard_end_unix']))))


def reconcile(root, name, python):
    inactive(root, name)
    arm = root / name
    control, source = arm / ('control_' + PHASE), arm / ('source_' + PHASE)
    require(read(control / 'READY.json')['passed'] and not (control / 'DISPATCHED.json').exists(), 'ready_once_only')
    receipt, plan = read(control / 'RECOVERY.json'), read(control / 'PLAN.json')
    require(time.time() < plan['hard_end_unix'] - 3600, 'fresh_remaining_budget')
    sys.path[:0] = [str(source), str(source / 'gpu'), str(root)]
    from gpu.r213_recovery_runtime import RecoveryJournal, saved_state
    class OfflineJournal(RecoveryJournal):
        def _reload_state(self, *arguments, **keywords):
            self.inbox = offline_inbox(plan)
            return super()._reload_state(*arguments, **keywords)
    moved = []
    for category in ('checkpoints', 'readouts'):
        for path in sorted((arm / 'raw' / category).glob('sleep_*')):
            if int(path.name.split('_')[1]) > receipt['complete_cycle']:
                destination = arm / PHASE / 'tail_artifacts' / category / path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
                moved.append(dict(relative=str(path.relative_to(arm)), preserved_relative=str(destination.relative_to(arm))))
    save(control / 'TAIL_ARTIFACTS_PRESERVED.json', dict(moved=moved, deleted=False))
    with OfflineJournal(arm / 'raw/stream') as journal:
        reference = journal.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(control / 'RECOVERY.json'),
            receipt_sha256=sha(control / 'RECOVERY.json'),
            state=saved_state(record(Path(receipt['complete_path'])), receipt['new_deadline_unix'])))
    save(control / 'RECOVERY_APPENDED.json', reference)
    cache = arm / 'raw/stream/correction_ledger.r233.tmp'
    save(cache, read(control / 'CORRECTION_CACHE_RECOVERY.json')['after'])
    os.replace(cache, arm / 'raw/stream/correction_ledger.json')
    save(control / 'RECONCILED.json', dict(recovery_record=reference, native_launched=False,
        observed_utc=utc(), cache_sha256=sha(arm / 'raw/stream/correction_ledger.json')))
    print(json.dumps(dict(life=name, status='RECONCILED_NOT_LAUNCHED', recovery_record=reference)))


def verify_reconciled(arm, control):
    expected = read(control / 'RECONCILED.json')['recovery_record']
    paths = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
    actual = record(paths[-1])
    require(actual['index'] == expected['index'] and actual['sha256'] == expected['sha256']
        and actual['kind'] == 'R213_SAVED_BOUNDARY_RECOVERY', 'exact_reconciled_head_no_new_native_activity')
    require(sha(arm / 'raw/stream/correction_ledger.json') == read(control / 'RECONCILED.json')['cache_sha256'],
        'reconciled_correction_cache_unchanged')


def launch(root, name, python):
    inactive(root, name)
    arm = root / name
    control = current_control(arm)
    source = Path(read(control / 'PLAN.json')['source_root'])
    require(read(control / 'READY.json')['passed'] and not (control / 'DISPATCHED.json').exists(), 'ready_once_only')
    require(time.time() < read(control / 'PLAN.json')['hard_end_unix'] - 3600, 'fresh_remaining_budget')
    verify_reconciled(arm, control)
    with (control / 'supervisor.log').open('x') as output:
        process = subprocess.Popen([python, '-B', '-m', 'gpu.r233_recovery_runtime', 'dispatch',
            '--config', str(control / 'GUARD.json')], cwd=source, env=environment(source, root),
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    save(control / 'DISPATCHED.json', dict(pid=process.pid, observed_utc=utc(), status='DISPATCHED_NOT_LOADED'))
    active = arm / 'ACTIVE_RUNTIME.r233.tmp'
    save(active, dict(source=str(source), control=str(control), module='gpu.r233_recovery_runtime',
        recovery_receipt=str(control / 'RECOVERY.json')))
    os.replace(active, arm / 'ACTIVE_RUNTIME.json')
    print(json.dumps(dict(life=name, status='DISPATCHED_NOT_LOADED', pid=process.pid)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('audit', 'prepare', 'reconcile', 'launch', 'retry_admission', 'adopt_policy', 'retry_policy', 'extend_prepared'))
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--name', choices=tuple(PROTECTED))
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--output', type=Path)
    options = parser.parse_args()
    if options.mode == 'audit':
        audit(options.root, options.output)
    else:
        globals()[options.mode](options.root, options.name, options.python)
