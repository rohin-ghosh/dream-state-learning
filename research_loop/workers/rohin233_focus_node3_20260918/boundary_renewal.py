"""Authorized next-COMPLETE handoff of four exact early-budget kept captions."""

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time

from recovery import (PHASE, conservative_ceiling, current_control, derived_budget_lease,
    environment, inactive, launch, manifest, manifest_python, offline_inbox, read,
    relocated_plan, require, utc)
from retirement import identity, metadata, PROTECTED, public_identity, record, save, sha


TARGETS = tuple(name for name, gpu in PROTECTED.items() if gpu in (0, 3, 5, 6))


def paths(arm):
    return sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))


def exact_native(expected, actual, control):
    require(all(actual[key] == expected[key] for key in ('pid', 'start_ticks', 'command_sha256'))
        and 'native' in actual['args'] and str(control / 'GUARD.json') in actual['args']
        and actual['state'] not in ('Z', 'X'), 'exact_owned_live_native_identity_required')


def selected(root, name):
    require(name in TARGETS, 'only_four_explicit_early_budget_captions')
    arm = root / name
    control = arm / ('control_' + PHASE + '_boundary_lease_ceiling')
    return arm, control, arm / ('source_' + PHASE + '_boundary_lease_ceiling')


def extension(plan, saved):
    require(plan['hard_end_unix'] > saved['state']['deadline_unix'], 'actual_forward_wall_extension')
    result = deepcopy(plan)
    result['authorized_wall_extension'] = dict(schema='R131_SAVED_STATE_WALL_EXTENSION_V1',
        previous_deadline_unix=saved['state']['deadline_unix'], previous_stream_sha256=saved['sha256'],
        new_deadline_unix=result['hard_end_unix'], lease_end_unix=result['lease_end_unix'],
        safety_margin_seconds=21600)
    return result


def prepare(root, name, python):
    arm, control, source = selected(root, name)
    old = current_control(arm)
    plan, guard = read(old / 'PLAN.json'), read(old / 'GUARD.json')
    require(plan['physical'] == PROTECTED[name] and not plan.get('authorized_wall_extension'),
        'only_original_short_budget_resident')
    loaded = next(record(path) for path in reversed(paths(arm)) if metadata(path) == 'LOADED')
    native = identity(loaded['document']['pid'])
    exact_native(native, identity(native['pid']), old)
    require(manifest_python(Path(plan['source_root'])) == guard['source_pins'], 'old_frozen_source_exact')
    control.mkdir(mode=0o700)
    shutil.copytree(Path(plan['source_root']), source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    candidate = relocated_plan(plan, source, conservative_ceiling(plan, guard, time.time()))
    overlay_pins = {}
    if plan.get('learn_row_policy') != 'R227_ALL_AUTHENTIC_CHILD_ROWS_V1':
        overlay = root / 'r227_policy_overlay'
        overlay_pins = read(overlay / 'MANIFEST.json')
        for relative, digest in overlay_pins.items():
            require(sha(overlay / relative) == digest, 'exact_tested_R227_overlay')
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(overlay / relative, target)
        reference = arm / 'source_r227_policy_ready'
        for relative in ('tests/test_orch_r205_reading_policy.py', 'organism_v6/orch_r225_content_target_filter.py'):
            if not (source / relative).exists():
                shutil.copy2(reference / relative, source / relative)
        sys.path[:0] = [str(root), str(source), str(source / 'gpu')]
        from r227_policy_stage import policy_plan
        candidate = policy_plan(candidate, source)
    tests = ['test_r205_runtime', 'test_r227_caption', 'test_orch_r227_learning_policy',
        'test_orch_r184_think_act_learn', 'test_orch_r205_reading_policy',
        'test_orch_r194_code_target_filter', 'test_orch_r195_learn_review_filter']
    with (control / 'CPU.log').open('x') as log:
        result = subprocess.run([python, '-B', '-m', 'unittest', '-q', *tests], cwd=source,
            env=environment(source, root), stdout=log, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'actual_receiving_CPU_gate_before_any_native_signal')
    save(control / 'DRAFT_PLAN.json', candidate)
    save(control / 'RECEIVING_CPU.json', dict(passed=True, tests=tests, source_pins=manifest_python(source),
        log_sha256=sha(control / 'CPU.log'), overlay_pins=overlay_pins, native_signals=0))
    save(control / 'PREPARED.json', dict(old_control=str(old), old_plan_sha256=sha(old / 'PLAN.json'),
        expected_native=native, prepared_utc=utc(), boundary_after_index=int(paths(arm)[-1].stem),
        source_pins=manifest_python(source), native_signals=0,
        authority='2026-09-18 explicit same-journal checkpoint-boundary horizon handoff'))
    print(json.dumps(dict(life=name, status='SOURCE_CPU_READY_NATIVE_UNTOUCHED', deadline_utc=utc(candidate['hard_end_unix']))))


def handoff(root, name, python):
    arm, control, source = selected(root, name)
    prepared = read(control / 'PREPARED.json')
    old = Path(prepared['old_control'])
    expected = prepared['expected_native']
    require(current_control(arm) == old and sha(old / 'PLAN.json') == prepared['old_plan_sha256'],
        'unchanged_old_runtime_no_overlapping_operator')
    require(manifest_python(source) == prepared['source_pins'], 'prepared_successor_source_exact')
    require(read(control / 'RECEIVING_CPU.json')['passed'], 'own_receiving_CPU_gate')
    require(not (control / 'HANDOFF_SIGNAL.json').exists(), 'one_explicit_handoff_no_retry')
    sys.path[:0] = [str(source), str(source / 'gpu'), str(root)]
    from gpu.r213_recovery_runtime import RecoveryJournal, saved_state
    from gpu.orch_r125_continual_native import NativeChild, prepare_wall_extension
    from organism_v6.orch_r125_continual_stream import ContinualStream, digest, verify_experiment_resume
    plan = read(control / 'DRAFT_PLAN.json')
    save(control / 'WAITING_NEXT_COMPLETE.json', dict(observed_utc=utc(), pid=os.getpid(),
        after_index=prepared['boundary_after_index'], deadline_unix=plan['hard_end_unix'],
        native_pauses=0, learner_runs_normally=True))
    complete_path = None
    while time.time() < plan['hard_end_unix']:
        exact_native(expected, identity(expected['pid']), old)
        candidates = [path for path in paths(arm)[-32:] if int(path.stem) > prepared['boundary_after_index']]
        for path in reversed(candidates):
            if metadata(path) == 'SLEEP_COMPLETE':
                complete = record(path)
                saved = saved_state(complete, complete['document']['resume_state']['state']['deadline_unix'])
                checkpoint_dir = arm / 'raw/checkpoints' / ('sleep_%06d' % complete['document']['cycle'])
                checkpoint = deepcopy(read(checkpoint_dir / 'COMMIT.json'))
                checkpoint.update(adapter_path=str(checkpoint_dir / 'adapter'), optimizer_rng_path=str(checkpoint_dir / 'optimizer_rng.pt'))
                NativeChild.verify_checkpoint(checkpoint)
                verify_experiment_resume(plan, saved['state']['experiment'])
                candidate = extension(plan, saved)
                prepare_wall_extension(candidate, ContinualStream.restore(saved, expected_sha256=saved['sha256']),
                    resume=True, plan_sha256=digest(candidate))
                complete_path = path
                break
        if complete_path is not None:
            break
        time.sleep(0.25)
    require(complete_path is not None, 'no_complete_no_native_signal')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        exact_native(expected, identity(expected['pid']), old)
        save(control / 'HANDOFF_SIGNAL.json', dict(observed_utc=utc(), observed_unix=time.time(),
            exact_native=public_identity(expected), checkpoint=dict(index=complete['index'], sha256=complete['sha256']),
            signal='SIGTERM', authorized_same_journal_handoff=True, SIGSTOP=False, holds=0))
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        require(bool(poller.poll(30000)), 'exact_old_exit_required_no_new_launch')
    finally:
        os.close(descriptor)
    save(control / 'OLD_EXIT_OBSERVED.json', dict(observed_utc=utc(), observed_unix=time.time(),
        **public_identity(expected), resident_continuity_claimed=False))
    end = time.time() + 30
    while not (old / 'EXIT.json').exists() and time.time() < end:
        time.sleep(0.25)
    exited = read(old / 'EXIT.json')
    require(exited['exit_code'] != 0, 'actual_handoff_outer_exit_required')
    inactive(root, name)
    all_paths = paths(arm)
    head = record(all_paths[-1])
    latest = next(path for path in reversed(all_paths) if metadata(path) == 'SLEEP_COMPLETE')
    require(latest == complete_path, 'selected_complete_remains_latest')
    preserved = arm / ('r233_boundary_lease_ceiling_preserved')
    preserved.mkdir(mode=0o700)
    for origin, target in ((arm / 'raw/stream', preserved / 'stream'),
            (checkpoint_dir, preserved / checkpoint_dir.name), (old, preserved / 'previous_control')):
        subprocess.run(['cp', '-a', '--reflink=auto', str(origin), str(target)], check=True)
    moved = []
    for category in ('checkpoints', 'readouts'):
        for path in sorted((arm / 'raw' / category).glob('sleep_*')):
            if int(path.name.split('_')[1]) > complete['document']['cycle']:
                destination = preserved / 'tail_artifacts' / category / path.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
                moved.append(dict(category=category, name=path.name))
    save(control / 'TAIL_ARTIFACTS_PRESERVED.json', dict(moved=moved, deleted=False))
    save(preserved / 'MANIFEST.json', manifest(preserved))
    import torch
    payload = torch.load(checkpoint_dir / 'optimizer_rng.pt', map_location='cpu', weights_only=False)
    require(payload['optimizer_steps'] == checkpoint['optimizer_steps'] and not torch.cuda.is_initialized(),
        'coherent_actual_optimizer_RNG_CPU_only')
    tail = [record(path) for path in all_paths if int(path.stem) > complete['index']]
    receipt = dict(old_native_absent=True, old_native_pid=expected['pid'], old_outer_exit_status=exited['exit_code'],
        exact_resident_continuity_claimed=False, old_head_index=head['index'], old_head_sha256=head['sha256'],
        complete_path=str(complete_path), complete_sha256=complete['sha256'],
        new_deadline_unix=saved['state']['deadline_unix'], target_operator_deadline_unix=plan['hard_end_unix'],
        complete_cycle=complete['document']['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        checkpoint_sha256=checkpoint['checkpoint_sha256'], preservation_manifest_sha256=sha(preserved / 'MANIFEST.json'),
        old_plan_sha256=sha(old / 'PLAN.json'), lost_tail_updates=sum(item['kind'] == 'UPDATE' for item in tail),
        tail_responses=[dict(index=item['index'], sha256=item['sha256']) for item in tail if item['kind'] == 'RESPONSE'],
        tail_inbox_ids=[item['document']['message']['id'] for item in tail if item['kind'] == 'INBOX'],
        same_journal=True, snapshot51_rebirth=False, planned_handoff_not_timeout_failure=True)
    save(control / 'RECOVERY.json', receipt)
    from r226_correction_boundary import select_cache
    corrections = [record(path) for path in all_paths if metadata(path) == 'R197_CORRECTION_CYCLE']
    cache = select_cache(corrections, complete)
    save(control / 'CORRECTION_CACHE_RECOVERY.json', dict(before=read(arm / 'raw/stream/correction_ledger.json'), after=cache))
    class OfflineJournal(RecoveryJournal):
        def _reload_state(self, *arguments, **keywords):
            self.inbox = offline_inbox(plan)
            return super()._reload_state(*arguments, **keywords)
    with OfflineJournal(arm / 'raw/stream') as journal:
        reference = journal.record('R213_SAVED_BOUNDARY_RECOVERY', dict(receipt_path=str(control / 'RECOVERY.json'),
            receipt_sha256=sha(control / 'RECOVERY.json'), state=saved))
        require(journal.latest_checkpoint()['document'] == saved, 'actual_CPU_same_journal_recovery')
    save(control / 'RECOVERY_APPENDED.json', reference)
    temporary = arm / 'raw/stream/correction_ledger.r233.boundary.tmp'
    save(temporary, cache)
    os.replace(temporary, arm / 'raw/stream/correction_ledger.json')
    save(control / 'RECONCILED.json', dict(recovery_record=reference, native_launched=False,
        observed_utc=utc(), cache_sha256=sha(arm / 'raw/stream/correction_ledger.json')))
    plan = extension(plan, saved)
    save(control / 'PLAN.json', plan)
    save(control / 'ARCHIVE_REPLAY.json', dict(verified=True, reference=reference,
        preserved_manifest_sha256=sha(preserved / 'MANIFEST.json'), existing_journal_checked_before_dispatch=True))
    save(control / 'LEASE.json', derived_budget_lease(read(old / 'LEASE.json'), plan['hard_end_unix'], sha(old / 'LEASE.json')))
    allocation = read(old / 'ALLOCATION.json')
    allocation.update(declared_unix=time.time(), plan_sha256=sha(control / 'PLAN.json'),
        cpu_receipt_path=str(control / 'RECEIVING_CPU.json'), cpu_receipt_sha256=sha(control / 'RECEIVING_CPU.json'))
    save(control / 'ALLOCATION.json', allocation)
    guard = read(old / 'GUARD.json')
    guard.update(attempt_dir=str(control), plan_path=str(control / 'PLAN.json'), plan_sha256=sha(control / 'PLAN.json'),
        source_pins=prepared['source_pins'], hard_end_unix=plan['hard_end_unix'],
        lease_path=str(control / 'LEASE.json'), lease_sha256=sha(control / 'LEASE.json'),
        allocation_path=str(control / 'ALLOCATION.json'), allocation_sha256=sha(control / 'ALLOCATION.json'))
    save(control / 'GUARD.json', guard)
    subprocess.run([python, '-B', '-c', 'from gpu.orch_r125_continual_guard import validate; import sys; validate(sys.argv[1])',
        str(control / 'GUARD.json')], cwd=source, env=environment(source, root), check=True, timeout=40)
    save(control / 'READY.json', dict(passed=True, actual_LOAD_pending=True, no_rebirth=True))
    active = arm / 'ACTIVE_RUNTIME.r233.boundary.tmp'
    save(active, dict(source=str(source), control=str(control), module='gpu.r233_recovery_runtime',
        recovery_receipt=str(control / 'RECOVERY.json')))
    os.replace(active, arm / 'ACTIVE_RUNTIME.json')
    launch(root, name, python)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'handoff'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--name', choices=TARGETS, required=True)
    parser.add_argument('--python', required=True)
    options = parser.parse_args()
    globals()[options.mode](options.root, options.name, options.python)
